"""Facade wiring security components for companion runtime."""
from __future__ import annotations

from dataclasses import dataclass, field

from om_ai.core.action_control import ActionRequest

from .audit_logger import SecurityAuditLogger
from .authorization import Authorization
from .input_validator import InputValidator
from .output_validator import OutputValidator
from .policy_engine import PolicyEngine
from .security_context import SecurityContext


@dataclass
class SecurityRuntime:
    policy: PolicyEngine = field(default_factory=PolicyEngine)
    authorization: Authorization = field(default_factory=Authorization)
    input_validator: InputValidator = field(default_factory=InputValidator)
    output_validator: OutputValidator = field(default_factory=OutputValidator)
    audit: SecurityAuditLogger = field(default_factory=SecurityAuditLogger)

    def guard_action(
        self, ctx: SecurityContext, request: ActionRequest
    ) -> tuple[bool, str]:
        ok, reason = self.authorization.can_execute_action(ctx, request)
        if not ok:
            self.audit.log("action_denied_boundary", {"reason": reason})
            return False, reason

        param_errors = self.input_validator.validate_action_parameters(
            request.parameters
        )
        if param_errors:
            reason = "; ".join(param_errors)
            self.audit.log("action_denied_params", {"reason": reason})
            return False, reason

        cap = request.action_type
        ok, reason = self.policy.evaluate_capability(ctx, cap)
        if not ok:
            self.audit.log("action_denied_capability", {"capability": cap})
            return False, reason

        fs_path = request.parameters.get("path")
        if fs_path is not None:
            ok, reason = self.policy.evaluate_path(str(fs_path))
            if not ok:
                self.audit.log("action_denied_path", {"path": str(fs_path)})
                return False, reason

        self.audit.log(
            "action_guard_pass",
            {"action_id": request.action_id, "action_type": request.action_type},
        )
        return True, ""
