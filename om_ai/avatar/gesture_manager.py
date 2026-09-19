from __future__ import annotations
from typing import Any

class GestureManager:
    def for_presence(self, presence: str) -> dict[str, Any]:
        table = {
            "attentive": "lean_in",
            "thinking": "nod_soft",
            "speaking": "open_presence",
            "concerned": "still",
            "excited": "lift",
            "waiting": "breathe",
        }
        return {"gesture": table.get(presence, "idle")}
