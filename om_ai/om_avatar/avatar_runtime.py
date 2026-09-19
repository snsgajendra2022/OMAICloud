from __future__ import annotations
from typing import Any

from .animation_controller import AnimationController
from .eye_tracking import EyeTracking
from .facial_controller import FacialController
from .gesture_engine import GestureEngine
from .lip_sync import LipSync

_RT = None

class OMAvatarRuntime:
    """Bridges OM brain state → 3D avatar (web Presence3D / Unity / Unreal)."""

    def __init__(self) -> None:
        self.animation = AnimationController()
        self.face = FacialController()
        self.lips = LipSync()
        self.eyes = EyeTracking()
        self.gestures = GestureEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "step": 106,
            "name": "OM 3D Avatar Runtime",
            "backends": ["web_threejs", "unity_vrm", "unreal_metahuman"],
        }

    def update(
        self,
        *,
        presence: str = "idle",
        mood: str = "neutral",
        speaking: bool = False,
        energy: float = 0.0,
        text: str = "",
    ) -> dict[str, Any]:
        pack = {
            "presence": presence,
            "animation": self.animation.clip_for(presence),
            "face": self.face.for_mood(mood or presence),
            "lips": {
                "jaw": self.lips.jaw_open(energy, speaking=speaking),
                "plan": self.lips.from_text(text, emotion=mood or presence) if (speaking and text) else None,
            },
            "eyes": self.eyes.look(presence),
            "gesture": self.gestures.for_state(presence),
            "text_len": len(text or ""),
        }
        # Also drive existing avatar engine if present
        try:
            from om_ai.avatar import get_avatar_engine
            pack["engine"] = get_avatar_engine().update(
                presence=presence, text=text, mood=mood
            )
        except Exception:
            pass
        return pack

def get_om_avatar() -> OMAvatarRuntime:
    global _RT
    if _RT is None:
        _RT = OMAvatarRuntime()
    return _RT
