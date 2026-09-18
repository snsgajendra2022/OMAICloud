"""Companion agent goals."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Goal:
    description: str
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed: bool = False

    def mark_complete(self) -> None:
        self.completed = True
