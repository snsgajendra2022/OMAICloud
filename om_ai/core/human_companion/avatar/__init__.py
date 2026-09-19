"""Avatar presence pack builder."""
from __future__ import annotations

from typing import Any

from .emotion_animation import EmotionAnimation
from .eye_tracking import EyeTracking
from .face_animation import FaceAnimation
from .lip_sync import LipSync


class AvatarRuntime:
    def __init__(self) -> None:
        self.face = FaceAnimation()
        self.lips = LipSync()
        self.eyes = EyeTracking()
        self.emotion_anim = EmotionAnimation()

    def build(
        self,
        *,
        speaking: bool = False,
        emotion: str = "neutral",
        presence: str = "attentive",
        spoken: str = "",
    ) -> dict[str, Any]:
        mode = "speaking" if speaking else presence
        return {
            "mode": mode,
            "presence": mode,
            "state": mode,
            "speaking": speaking,
            "face": self.face.for_emotion(emotion),
            "expression": self.emotion_anim.map(emotion),
            "eyes": self.eyes.plan(mode),
            "lips": self.lips.plan(spoken) if speaking or spoken else {"jaw": 0.0},
            "animation": mode,
            "gesture": "attentive" if mode == "attentive" else "",
        }
