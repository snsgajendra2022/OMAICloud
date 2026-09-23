"""Avatar state — listening / thinking / speaking."""
from __future__ import annotations

from typing import Any


class AvatarState:
    PHASES = ("listening", "thinking", "speaking", "waiting")

    def resolve(self, *, emotion: str = "neutral", phase: str = "listening") -> dict[str, Any]:
        phase = phase if phase in self.PHASES else "listening"
        expression = {
            "listening": "attentive",
            "thinking": "focused",
            "speaking": "warm",
            "waiting": "calm",
        }.get(phase, "attentive")
        if emotion in {"sad", "tired", "fatigue", "stressed"}:
            expression = "soft"
        elif emotion in {"happy", "excited"}:
            expression = "bright"
        elif emotion in {"angry", "frustrated"}:
            expression = "steady"
        return {
            "phase": phase,
            "expression": expression,
            "emotion": emotion,
            "lip_sync": phase == "speaking",
        }
