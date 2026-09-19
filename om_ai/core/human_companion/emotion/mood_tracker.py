"""Mood tracker — rolling emotional state across turns."""
from __future__ import annotations

from collections import deque
from typing import Any


class MoodTracker:
    def __init__(self, window: int = 8) -> None:
        self._window: deque[str] = deque(maxlen=window)
        self._mood = "neutral"

    def update(self, emotion: str) -> dict[str, Any]:
        label = (emotion or "neutral").strip().lower() or "neutral"
        self._window.append(label)
        # Dominant non-neutral wins; else neutral
        counts: dict[str, int] = {}
        for e in self._window:
            if e != "neutral":
                counts[e] = counts.get(e, 0) + 1
        if counts:
            self._mood = max(counts, key=counts.get)  # type: ignore[arg-type]
        else:
            self._mood = "neutral"
        return {"mood": self._mood, "recent": list(self._window), "label": label}
