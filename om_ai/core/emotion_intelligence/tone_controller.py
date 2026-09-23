"""Tone controller — maps emotion → speaking tone (empathy, not fake feelings)."""
from __future__ import annotations

from typing import Any

from .response_tone import ResponseTone


class ToneController(ResponseTone):
    def for_emotion(self, emotion: str, *, need: str = "") -> dict[str, Any]:
        pack = self.select(emotion, need=need or "steady")
        pack["emotion"] = emotion
        return pack

    def apply(self, emotion: str) -> dict[str, Any]:
        return self.for_emotion(emotion)
