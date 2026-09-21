"""Attention manager — where OM's focus is."""
from __future__ import annotations

from typing import Any

from .availability_state import AvailabilityState


class AttentionManager:
    def __init__(self) -> None:
        self.focus = "user"
        self.intensity = 0.6

    def on_phase(self, phase: AvailabilityState) -> dict[str, Any]:
        mapping = {
            AvailabilityState.WAITING: ("environment", 0.35),
            AvailabilityState.LISTENING: ("user", 0.9),
            AvailabilityState.THINKING: ("task", 0.75),
            AvailabilityState.RESPONDING: ("user", 0.85),
            AvailabilityState.INTERRUPTED: ("user", 1.0),
            AvailabilityState.READY: ("user", 0.5),
        }
        self.focus, self.intensity = mapping.get(phase, ("user", 0.5))
        return {"focus": self.focus, "intensity": self.intensity, "phase": phase.value}
