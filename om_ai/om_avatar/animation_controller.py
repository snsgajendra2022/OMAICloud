from __future__ import annotations
from typing import Any

class AnimationController:
    def clip_for(self, state: str) -> dict[str, Any]:
        s = (state or "idle").lower()
        return {"clip": s, "loop": s in {"idle", "listening", "waiting"}, "blend": 0.35}
