"""Topic tracker for human-context layer."""
from __future__ import annotations

import re
from typing import Any


class TopicTracker:
    _TOPICS: list[tuple[str, re.Pattern[str]]] = [
        ("work_stress", re.compile(r"(?i)\b(work|office|deadline|meeting|boss|client)\b")),
        ("coding", re.compile(r"(?i)\b(bug|server|code|deploy|api|error|stack|git)\b")),
        ("health", re.compile(r"(?i)\b(sleep|tired|sick|headache|health|rest)\b")),
        ("personal", re.compile(r"(?i)\b(family|friend|home|relationship)\b")),
        ("day_life", re.compile(r"(?i)\b(today|yesterday|morning|evening|day)\b")),
    ]

    def __init__(self) -> None:
        self.current = "general"
        self.history: list[str] = []

    def update(self, message: str, *, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        del history
        low = (message or "").lower()
        topic = "general"
        for name, pat in self._TOPICS:
            if pat.search(low):
                topic = name
                break
        if topic != "general":
            self.current = topic
            self.history.append(topic)
            self.history = self.history[-12:]
        return {"topic": self.current, "history": list(self.history)}
