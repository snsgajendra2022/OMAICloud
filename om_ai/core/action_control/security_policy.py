"""High-level security policy for action control."""
from __future__ import annotations

from dataclasses import dataclass, field

from .action_request import ActionRequest, RiskClass


@dataclass
class SecurityPolicy:
    """Operator-tunable policy knobs."""

    block_external_authorization: bool = True
    max_destructive_per_session: int = 3
    require_approval_for_external_side_effects: bool = True
    allowed_action_prefixes: tuple[str, ...] = field(
        default_factory=lambda: (
            "command.",
            "filesystem.",
            "application.",
            "browser.",
            "process.",
            "system.",
        )
    )

    def evaluate(self, request: ActionRequest) -> tuple[bool, str]:
        if not request.action_type:
            return False, "empty action_type"

        if not any(
            request.action_type.startswith(p) for p in self.allowed_action_prefixes
        ):
            return False, f"action_type not allowed: {request.action_type}"

        if self.block_external_authorization and request.source == "external":
            auth_keys = {"approve", "grant", "authorize", "permission"}
            if request.action_type in auth_keys or any(
                k in request.parameters for k in auth_keys
            ):
                return False, "external content cannot authorize actions"

        if (
            self.require_approval_for_external_side_effects
            and request.risk_class == RiskClass.EXTERNAL_SIDE_EFFECT
            and request.source == "external"
        ):
            return False, "external-sourced side effects require internal actor"

        return True, ""
