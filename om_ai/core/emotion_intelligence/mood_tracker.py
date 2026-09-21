"""Mood tracker — rolling emotional state across turns."""
from __future__ import annotations

from typing import Any


class MoodTracker:
    def __init__(self) -> None:
        self.mood = "neutral"
        self.streak = 0
        self._last = "neutral"

    def update(self, emotion: str) -> dict[str, Any]:
        e = (emotion or "neutral").lower()
        if e == self._last:
            self.streak += 1
        else:
            self.streak = 1
            self._last = e
        # Map momentary emotion → sustained mood
        if e in {"frustrated", "stressed", "masked_stress", "sad", "tired"}:
            self.mood = "low" if self.streak >= 2 else e
        elif e in {"happy", "excited"}:
            self.mood = "up"
        else:
            self.mood = "steady" if self.mood == "neutral" else self.mood
        return {"mood": self.mood, "streak": self.streak, "last_emotion": e}
