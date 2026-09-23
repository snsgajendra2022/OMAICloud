"""Emotion state — tracked affect trail (OM understands; does not claim to feel)."""
from __future__ import annotations

from typing import Any


class EmotionState:
    def __init__(self) -> None:
        self.current = "neutral"
        self.confidence = 0.55
        self.history: list[str] = []

    def update(self, emotion: str, *, confidence: float = 0.55) -> dict[str, Any]:
        e = (emotion or "neutral").strip() or "neutral"
        self.current = e
        self.confidence = float(confidence)
        self.history.append(e)
        self.history = self.history[-12:]
        return {
            "emotion": self.current,
            "confidence": self.confidence,
            "recent": list(self.history[-5:]),
            # Honesty contract
            "om_pretends_feelings": False,
            "om_empathy": True,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "emotion": self.current,
            "confidence": self.confidence,
            "recent": list(self.history[-5:]),
        }
