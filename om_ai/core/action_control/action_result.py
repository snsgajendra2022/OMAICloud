"""Action execution outcomes."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionStatus(str, Enum):
    PENDING = "pending"
    NEEDS_APPROVAL = "needs_approval"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionResult(BaseModel):
    action_id: str
    status: ActionStatus
    output: Any = None
    error: str | None = None
    audit_ref: str | None = None
    risk_class: str | None = None
    action_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
