"""Single companion conversation session state."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ConversationSession:
    session_id: str
    tenant_id: str = "default"
    actor: str = ""
    project_id: str = ""
    created_at: str = field(default_factory=_utc_now)
    turn_count: int = 0
    last_semantic: dict[str, Any] = field(default_factory=dict)
    interrupted: bool = False

    @property
    def user_key(self) -> str:
        return f"{self.tenant_id}:{self.actor or 'anon'}"

    @property
    def session_key(self) -> str:
        return self.session_id

    def bump_turn(self) -> None:
        self.turn_count += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "actor": self.actor,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "turn_count": self.turn_count,
            "interrupted": self.interrupted,
        }
