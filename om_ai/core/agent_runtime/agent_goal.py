"""Agent goals for the autonomous runtime."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass
class AgentGoal:
    """A measurable objective an agent (or team) should achieve."""

    description: str
    priority: float = 0.5
    status: str = "open"  # open | in_progress | done | failed
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    owner: str = ""
    success_criteria: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def mark(self, status: str) -> "AgentGoal":
        self.status = status
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "owner": self.owner,
            "success_criteria": list(self.success_criteria),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }
