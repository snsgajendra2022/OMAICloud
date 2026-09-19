from __future__ import annotations
from typing import Any

class AnimationController:
    def clip(self, presence: str, *, glow: float = 0.5) -> dict[str, Any]:
        speed = {
            "thinking": 0.55,
            "remembering": 0.5,
            "concerned": 0.45,
            "excited": 1.25,
            "speaking": 1.0,
            "silent_listening": 0.7,
            "attentive": 0.8,
        }.get(presence, 0.65)
        return {
            "clip": f"presence_{presence or 'idle'}",
            "speed": speed,
            "glow": glow,
            "loop": True,
        }
