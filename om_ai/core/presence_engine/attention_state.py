"""Rich companion presence modes — beyond listening/thinking/speaking."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PresenceMode(str, Enum):
    IDLE = "idle"
    ATTENTIVE = "attentive"
    CURIOUS = "curious"
    THINKING = "thinking"
    REMEMBERING = "remembering"
    EXPLAINING = "explaining"
    WAITING = "waiting"
    CONFUSED = "confused"
    EXCITED = "excited"
    CONCERNED = "concerned"
    FOCUSED = "focused"
    SILENT_LISTENING = "silent_listening"
    SPEAKING = "speaking"


@dataclass
class AttentionState:
    mode: PresenceMode = PresenceMode.IDLE
    intensity: float = 0.4  # 0..1
    focus_target: str = "user"
    since_ms: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "intensity": round(self.intensity, 3),
            "focus_target": self.focus_target,
            "since_ms": self.since_ms,
            "meta": dict(self.meta),
        }
