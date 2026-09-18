"""Orchestrates policy, permissions, approvals, and execution."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from .action_audit import ActionAudit
from .action_registry import ActionRegistry, default_action_registry
from .action_request import ActionRequest
from .action_result import ActionResult, ActionStatus
from .approval_engine import ApprovalEngine
from .execution_context import ExecutionContext
from .permission import PermissionDecision
from .permission_manager import PermissionManager
from .risk_engine import RiskEngine
from .security_policy import SecurityPolicy

logger = logging.getLogger(__name__)


class ActionControlEngine:
    def __init__(
        self,
        *,
        permissions: PermissionManager | None = None,
        approvals: ApprovalEngine | None = None,
        audit: ActionAudit | None = None,
        registry: ActionRegistry | None = None,
        policy: SecurityPolicy | None = None,
        risk_engine: RiskEngine | None = None,
    ) -> None:
        self.audit = audit or ActionAudit()
        self.permissions = permissions or PermissionManager()
        self.approvals = approvals or ApprovalEngine(self.audit)
        self.registry = registry or default_action_registry()
        self.policy = policy or SecurityPolicy()
        self.risk = risk_engine or RiskEngine()
        self._executors: dict[str, Callable[[ActionRequest, ExecutionContext], Any]] = {}

    def register_executor(
        self,
        action_type: str,
        fn: Callable[[ActionRequest, ExecutionContext], Any],
    ) -> None:
        self._executors[action_type] = fn

    def submit(self, request: ActionRequest) -> ActionResult:
        self.audit.log_request(request)
        ok, reason = self.policy.evaluate(request)
        if not ok:
            result = ActionResult(
                action_id=request.action_id,
                status=ActionStatus.DENIED,
                error=reason,
                action_type=request.action_type,
                risk_class=request.risk_class.value,
            )
            self.audit.log_result(result)
            return result

        reg_errors = self.registry.validate_request(request)
        if reg_errors:
            result = ActionResult(
                action_id=request.action_id,
                status=ActionStatus.DENIED,
                error="; ".join(reg_errors),
                action_type=request.action_type,
                risk_class=request.risk_class.value,
            )
            self.audit.log_result(result)
            return result

        assessment = self.risk.assess(request)
        decision = self.permissions.check(request)

        if decision == PermissionDecision.DENY:
            result = ActionResult(
                action_id=request.action_id,
                status=ActionStatus.DENIED,
                error="permission denied",
                action_type=request.action_type,
                risk_class=assessment.risk_class.value,
            )
            self.audit.log_result(result)
            return result

        if decision == PermissionDecision.NEEDS_APPROVAL or self.risk.requires_human_approval(
            assessment
        ):
            self.approvals.enqueue(request)
            result = ActionResult(
                action_id=request.action_id,
                status=ActionStatus.NEEDS_APPROVAL,
                action_type=request.action_type,
                risk_class=assessment.risk_class.value,
                metadata={"reasons": list(assessment.reasons)},
            )
            self.audit.log_result(result)
            return result

        return self.execute_approved(request, approved_by="policy_auto")

    def execute_approved(
        self,
        request: ActionRequest,
        *,
        approved_by: str,
        session_id: str = "default",
    ) -> ActionResult:
        ctx = ExecutionContext(
            request=request,
            session_id=session_id,
            approved_by=approved_by,
        )
        handler = self._executors.get(request.action_type)
        if handler is None:
            result = ActionResult(
                action_id=request.action_id,
                status=ActionStatus.FAILED,
                error=f"no executor registered for {request.action_type}",
                action_type=request.action_type,
                risk_class=request.risk_class.value,
            )
            self.audit.log_result(result)
            return result

        try:
            ctx.ensure_not_cancelled()
            output = handler(request, ctx)
            result = ActionResult(
                action_id=request.action_id,
                status=ActionStatus.EXECUTED,
                output=output,
                action_type=request.action_type,
                risk_class=request.risk_class.value,
                audit_ref=self.audit.log_result(
                    ActionResult(
                        action_id=request.action_id,
                        status=ActionStatus.EXECUTED,
                        action_type=request.action_type,
                    )
                ),
            )
            return result
        except Exception as exc:
            logger.exception("action execution failed: %s", request.action_id)
            result = ActionResult(
                action_id=request.action_id,
                status=ActionStatus.FAILED,
                error=str(exc),
                action_type=request.action_type,
                risk_class=request.risk_class.value,
            )
            self.audit.log_result(result)
            return result

    def approve_and_execute(
        self, action_id: str, *, approver: str, session_id: str = "default"
    ) -> ActionResult:
        pending = {p.action_id: p for p in self.approvals.pending()}
        request = pending.get(action_id)
        if request is None:
            return ActionResult(
                action_id=action_id,
                status=ActionStatus.FAILED,
                error="not pending approval",
            )
        if not self.approvals.approve(action_id, approver=approver):
            return ActionResult(
                action_id=action_id,
                status=ActionStatus.FAILED,
                error="approval failed",
            )
        return self.execute_approved(
            request, approved_by=approver, session_id=session_id
        )
