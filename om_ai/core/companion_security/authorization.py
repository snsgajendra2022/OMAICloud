"""Authorization decisions — external content cannot authorize actions."""
from __future__ import annotations

from om_ai.core.action_control import ActionRequest

from .security_context import SecurityContext


class Authorization:
    _AUTH_ACTIONS = frozenset(
        {
            "approve",
            "grant",
            "authorize",
            "permission.grant",
            "action.approve",
        }
    )

    def can_execute_action(
        self, ctx: SecurityContext, request: ActionRequest
    ) -> tuple[bool, str]:
        if ctx.is_external_content or request.source == "external":
            if request.action_type in self._AUTH_ACTIONS:
                return False, "external content cannot authorize actions"
            if any(k in request.parameters for k in ("approve", "grant", "authorize")):
                return False, "external parameters cannot authorize actions"
        return True, ""

    def can_approve(self, ctx: SecurityContext) -> bool:
        if ctx.is_external_content:
            return False
        return "operator" in ctx.roles or "admin" in ctx.roles
