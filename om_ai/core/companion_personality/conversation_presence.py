"""Conversation presence — listening / speaking state for the voice layer."""
from __future__ import annotations

from typing import Any


class ConversationPresence:
    """Tracks how OM should *sound* present — not what to say."""

    def __init__(self) -> None:
        self.mode = "listening"

    def on_user(self, emotion: str = "neutral") -> dict[str, Any]:
        if emotion in {"tired", "sad", "stress"}:
            self.mode = "attentive"
        else:
            self.mode = "listening"
        return {"mode": self.mode, "emotion": emotion}

    def on_assistant(self, *, speaking: bool = True) -> dict[str, Any]:
        self.mode = "speaking" if speaking else "waiting"
        return {"mode": self.mode}

    def to_dict(self) -> dict[str, Any]:
        return {"mode": self.mode}
