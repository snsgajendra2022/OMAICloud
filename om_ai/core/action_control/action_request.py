"""Structured action requests with schema validation."""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class RiskClass(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW_IMPACT = "LOW_IMPACT"
    REVERSIBLE_WRITE = "REVERSIBLE_WRITE"
    EXTERNAL_SIDE_EFFECT = "EXTERNAL_SIDE_EFFECT"
    SENSITIVE = "SENSITIVE"
    DESTRUCTIVE = "DESTRUCTIVE"


_AUTO_ALLOW_RISKS = frozenset({RiskClass.READ_ONLY, RiskClass.LOW_IMPACT})


class ActionRequest(BaseModel):
    """Validated action intent; extra fields are rejected."""

    model_config = {"extra": "forbid"}

    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = Field(..., min_length=1, max_length=256)
    risk_class: RiskClass
    parameters: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="system", min_length=1, max_length=128)
    source: str = Field(
        default="internal",
        description="internal | external — external cannot self-authorize",
    )
    reason: str = Field(default="", max_length=4096)
    requires_explicit_approval: bool | None = None
    correlation_id: str | None = None

    @field_validator("action_type")
    @classmethod
    def normalize_action_type(cls, v: str) -> str:
        return v.strip()

    @field_validator("source")
    @classmethod
    def normalize_source(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"internal", "external"}:
            raise ValueError("source must be 'internal' or 'external'")
        return s

    @model_validator(mode="after")
    def set_default_approval(self) -> ActionRequest:
        if self.requires_explicit_approval is None:
            self.requires_explicit_approval = (
                self.risk_class not in _AUTO_ALLOW_RISKS
            )
        return self

    def is_auto_eligible(self) -> bool:
        return (
            not self.requires_explicit_approval
            and self.risk_class in _AUTO_ALLOW_RISKS
            and self.source == "internal"
        )
