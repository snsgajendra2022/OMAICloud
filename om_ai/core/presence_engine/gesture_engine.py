"""Lightweight gesture cues for avatar / HUD."""
from __future__ import annotations

from typing import Any

from .attention_state import PresenceMode


class GestureEngine:
    def cue(self, mode: PresenceMode) -> dict[str, Any]:
        table = {
            PresenceMode.ATTENTIVE: {"gesture": "lean_in", "duration_ms": 400},
            PresenceMode.THINKING: {"gesture": "nod_soft", "duration_ms": 600},
            PresenceMode.SPEAKING: {"gesture": "open_hand", "duration_ms": 0},
            PresenceMode.CONCERNED: {"gesture": "still", "duration_ms": 800},
            PresenceMode.EXCITED: {"gesture": "lift", "duration_ms": 350},
            PresenceMode.WAITING: {"gesture": "breathe", "duration_ms": 1200},
        }
        return table.get(mode, {"gesture": "idle", "duration_ms": 0})
