"""Gesture engine adapter."""
from __future__ import annotations

from typing import Any


class GestureEngine:
    def for_phase(self, phase: str) -> dict[str, Any]:
        try:
            from om_ai.core.presence_engine.gesture_engine import GestureEngine as GE

            ge = GE()
            if hasattr(ge, "for_phase"):
                return ge.for_phase(phase)
            if hasattr(ge, "map"):
                return ge.map(phase)
        except Exception:
            pass
        return {"phase": phase, "gesture": "idle"}
