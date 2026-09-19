"""Decide presence mode from user text + brain signals."""
from __future__ import annotations

import re
import time
from typing import Any

from .attention_state import AttentionState, PresenceMode
from .expression_state import expression_for
from .gesture_engine import GestureEngine
from .mood_context import MoodContext


class PresenceManager:
    def __init__(self) -> None:
        self.state = AttentionState()
        self.mood = MoodContext()
        self.gestures = GestureEngine()
        self._t0 = time.time()

    def set_mode(self, mode: PresenceMode | str, *, intensity: float | None = None) -> dict[str, Any]:
        if isinstance(mode, str):
            mode = PresenceMode(mode)
        self.state.mode = mode
        if intensity is not None:
            self.state.intensity = max(0.0, min(1.0, intensity))
        self.state.since_ms = (time.time() - self._t0) * 1000
        expr = expression_for(mode, mood=self.mood.label)
        gest = self.gestures.cue(mode)
        return {
            "presence": self.state.to_dict(),
            "expression": expr.to_dict(),
            "gesture": gest,
            "mood": self.mood.to_dict(),
        }

    def react_to_user(self, text: str, *, affect: dict[str, Any] | None = None) -> dict[str, Any]:
        low = (text or "").lower()
        affect = affect or {}
        if affect.get("label"):
            self.mood.update(
                label=str(affect["label"]),
                valence=float(affect.get("valence") or 0),
                arousal=float(affect.get("arousal") or 0.35),
            )

        if re.search(r"(?i)\b(problem|issue|error|bug|stuck|fail|broken|परेशान|problem)\b", low):
            return self.set_mode(PresenceMode.ATTENTIVE, intensity=0.75)
        if re.search(r"(?i)\b(why|how|what if|curious|explain|क्यों|कैसे)\b", low):
            return self.set_mode(PresenceMode.CURIOUS, intensity=0.65)
        if re.search(r"(?i)\b(remember|last time|yesterday|याद)\b", low):
            return self.set_mode(PresenceMode.REMEMBERING, intensity=0.6)
        if self.mood.label in {"concerned", "frustrated"}:
            return self.set_mode(PresenceMode.CONCERNED, intensity=0.7)
        if self.mood.label in {"engaged_positive", "positive"}:
            return self.set_mode(PresenceMode.EXCITED, intensity=0.65)
        if len((text or "").split()) <= 3:
            return self.set_mode(PresenceMode.SILENT_LISTENING, intensity=0.55)
        return self.set_mode(PresenceMode.ATTENTIVE, intensity=0.6)

    def on_thinking(self) -> dict[str, Any]:
        return self.set_mode(PresenceMode.THINKING, intensity=0.7)

    def on_speaking(self) -> dict[str, Any]:
        return self.set_mode(PresenceMode.SPEAKING, intensity=0.8)

    def on_listening(self) -> dict[str, Any]:
        return self.set_mode(PresenceMode.SILENT_LISTENING, intensity=0.55)

    def snapshot(self) -> dict[str, Any]:
        expr = expression_for(self.state.mode, mood=self.mood.label)
        return {
            "presence": self.state.to_dict(),
            "expression": expr.to_dict(),
            "gesture": self.gestures.cue(self.state.mode),
            "mood": self.mood.to_dict(),
        }
