"""STEP 54 Avatar brain — presence → expression → animation."""
from __future__ import annotations

from typing import Any

from .animation_controller import AnimationController
from .avatar_state import AvatarState
from .eye_tracking import EyeTracking
from .facial_expression import FacialExpression
from .gesture_manager import GestureManager
from .lip_sync import LipSync

_ENGINE = None


class AvatarEngine:
    def __init__(self) -> None:
        self.state = AvatarState()
        self.face = FacialExpression()
        self.lips = LipSync()
        self.eyes = EyeTracking()
        self.gestures = GestureManager()
        self.anim = AnimationController()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 54, "name": "Avatar Intelligence", "state": self.state.to_dict()}

    def update(self, *, presence: str = "idle", text: str = "", mood: str = "neutral") -> dict[str, Any]:
        fx = self.face.resolve(presence)
        self.state.expression = fx["expression"]
        self.state.eyes = fx["eyes"]
        self.state.pose = presence or "idle"
        self.state.attention = 0.75 if presence in {"attentive", "focused", "speaking"} else 0.45
        self.state.glow = 0.7 if presence == "speaking" else 0.5
        pack = {
            "state": self.state.to_dict(),
            "face": fx,
            "eyes": self.eyes.focus(presence=presence),
            "gesture": self.gestures.for_presence(presence),
            "animation": self.anim.clip(presence, glow=self.state.glow),
            "lip_sync": self.lips.envelope(text) if presence == "speaking" else None,
            "mood": mood,
        }
        return pack


def get_avatar_engine() -> AvatarEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = AvatarEngine()
    return _ENGINE
