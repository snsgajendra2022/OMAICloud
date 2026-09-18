"""Active voice conversation session (wake once, multi-turn)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any
import uuid


@dataclass
class VoiceSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    active: bool = False
    muted: bool = False
    pending_permission_id: str | None = None
    pending_action: dict[str, Any] | None = None
    last_user_text: str = ""
    last_assistant_text: str = ""
    interrupted_assistant_text: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    timeout_seconds: float = 45.0
    history: list[dict[str, str]] = field(default_factory=list)
    # Soft conversation context for coreference (not ambient audio)
    last_project_hint: str = ""
    last_app_hint: str = ""
    last_path_hint: str = ""

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def expired(self) -> bool:
        if not self.active:
            return True
        return datetime.now(timezone.utc) - self.last_activity > timedelta(seconds=self.timeout_seconds)

    def activate(self) -> None:
        self.active = True
        self.touch()

    def deactivate(self) -> None:
        self.active = False
        self.pending_permission_id = None
        self.pending_action = None

    def add_turn(self, role: str, content: str) -> None:
        text = (content or "").strip()
        if not text:
            return
        self.history.append({"role": role, "content": text[:4000]})
        if role == "user":
            self.last_user_text = text
        else:
            self.last_assistant_text = text
        self.touch()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "active": self.active,
            "muted": self.muted,
            "pending_permission_id": self.pending_permission_id,
            "history_turns": len(self.history),
            "last_activity": self.last_activity.isoformat(),
            "timeout_seconds": self.timeout_seconds,
        }
