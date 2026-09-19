from __future__ import annotations
from typing import Any

class EyeTracking:
    def look(self, presence: str = "idle") -> dict[str, Any]:
        if presence in {"attentive", "listening"}:
            return {"x": 0.0, "y": 0.02, "blink_rate": 0.15}
        return {"x": 0.0, "y": 0.0, "blink_rate": 0.08}
