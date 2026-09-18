"""Permission grants and decisions."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .action_request import RiskClass


class PermissionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    NEEDS_APPROVAL = "needs_approval"


class Permission(BaseModel):
    subject: str = Field(..., min_length=1)
    action_type: str = Field(..., min_length=1)
    risk_class: RiskClass
    decision: PermissionDecision
    granted_by: str = Field(default="operator")
    expires_at: datetime | None = None
    scope: dict[str, Any] = Field(default_factory=dict)
    grant_id: str | None = None

    def is_active(self, now: datetime | None = None) -> bool:
        if self.decision != PermissionDecision.ALLOW:
            return False
        if self.expires_at is None:
            return True
        ts = now or datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return ts <= exp
