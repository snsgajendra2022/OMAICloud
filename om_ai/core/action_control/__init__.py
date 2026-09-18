"""Action control — permissions, approvals, audit, safe execution."""
from __future__ import annotations

from .action_audit import ActionAudit
from .action_control_engine import ActionControlEngine
from .action_registry import ActionRegistry, ActionSpec, default_action_registry
from .action_request import ActionRequest, RiskClass
from .action_result import ActionResult, ActionStatus
from .approval_engine import ApprovalEngine
from .command_executor import CommandExecutor
from .execution_context import ExecutionContext
from .permission import Permission, PermissionDecision
from .permission_manager import PermissionManager
from .risk_engine import RiskAssessment, RiskEngine
from .security_policy import SecurityPolicy

__all__ = [
    "ActionAudit",
    "ActionControlEngine",
    "ActionRegistry",
    "ActionRequest",
    "ActionResult",
    "ActionSpec",
    "ActionStatus",
    "ApprovalEngine",
    "CommandExecutor",
    "ExecutionContext",
    "Permission",
    "PermissionDecision",
    "PermissionManager",
    "RiskAssessment",
    "RiskClass",
    "RiskEngine",
    "SecurityPolicy",
    "default_action_registry",
]
