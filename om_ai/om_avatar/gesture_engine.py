from __future__ import annotations
from typing import Any

class GestureEngine:
    def for_state(self, state: str) -> dict[str, Any]:
        s = (state or "idle").lower()
        if s in {"attentive", "listening"}:
            return {"arms": "open", "lean": 0.05}
        if s == "explaining":
            return {"arms": "present", "lean": 0.02}
        return {"arms": "neutral", "lean": 0.0}
