"""Short-term dialogue memory for continuous conversation."""
from __future__ import annotations

from typing import Any


class DialogueMemory:
    def __init__(self) -> None:
        self.last_user: str = ""
        self.last_assistant: str = ""
        self.thread_summary: str = ""
        self.entities: dict[str, str] = {}

    def remember(self, role: str, text: str) -> None:
        if role == "user":
            self.last_user = text
        else:
            self.last_assistant = text

    def remember_entity(self, key: str, value: str) -> None:
        if key and value:
            self.entities[key] = value[:200]

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_user": self.last_user,
            "last_assistant": self.last_assistant,
            "thread_summary": self.thread_summary,
            "entities": dict(self.entities),
        }
