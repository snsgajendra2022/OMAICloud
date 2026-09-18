"""Mutable context for a single action execution attempt."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .action_request import ActionRequest


@dataclass
class ExecutionContext:
    request: ActionRequest
    session_id: str = "default"
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: str | None = None
    approval_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False

    def mark_cancelled(self) -> None:
        self.cancelled = True

    def ensure_not_cancelled(self) -> None:
        if self.cancelled:
            raise RuntimeError("execution cancelled")
