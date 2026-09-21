"""Emotional context across the conversation."""
from __future__ import annotations

from typing import Any


class EmotionalContext:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def push(self, pack: dict[str, Any]) -> None:
        self._events.append(pack)
        self._events = self._events[-20:]

    def summary(self) -> dict[str, Any]:
        if not self._events:
            return {"recent": [], "dominant": "neutral"}
        labels = [str(e.get("emotion") or "neutral") for e in self._events[-5:]]
        dominant = max(set(labels), key=labels.count)
        return {"recent": labels, "dominant": dominant, "count": len(self._events)}
