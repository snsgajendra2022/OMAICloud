"""Conversation state for continuous companion dialogue."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationState:
    session_id: str = "default"
    turn_count: int = 0
    active_topic: str = "general"
    last_user: str = ""
    last_assistant: str = ""
    pending_reference: str = ""  # resolved "it/that/this"
    open_threads: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    interrupted: bool = False

    def bump(self, user: str, assistant: str = "") -> None:
        self.turn_count += 1
        if user:
            self.last_user = user
        if assistant:
            self.last_assistant = assistant

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "active_topic": self.active_topic,
            "last_user": self.last_user[:200],
            "last_assistant": self.last_assistant[:200],
            "pending_reference": self.pending_reference,
            "open_threads": list(self.open_threads)[-5:],
            "goals": list(self.goals)[-5:],
            "interrupted": self.interrupted,
        }
