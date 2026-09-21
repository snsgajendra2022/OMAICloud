"""Short dialogue memory for human-context continuity."""
from __future__ import annotations

from typing import Any


class DialogueMemory:
    def __init__(self, maxlen: int = 16) -> None:
        self.maxlen = maxlen
        self._turns: list[dict[str, str]] = []
        self.open_thread: str = ""
        self.last_topic: str = "general"

    def remember(self, user: str, assistant: str = "", *, topic: str = "") -> None:
        self._turns.append({"role": "user", "text": (user or "")[:500]})
        if assistant:
            self._turns.append({"role": "assistant", "text": (assistant or "")[:500]})
        self._turns = self._turns[-self.maxlen :]
        if topic:
            self.last_topic = topic
            self.open_thread = topic

    def recent(self, n: int = 6) -> list[dict[str, str]]:
        return list(self._turns[-n:])

    def blob(self) -> str:
        lines = [f"{t['role']}: {t['text']}" for t in self.recent(6)]
        if self.open_thread:
            lines.insert(0, f"open_thread: {self.open_thread}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "turns": self.recent(),
            "open_thread": self.open_thread,
            "last_topic": self.last_topic,
        }
