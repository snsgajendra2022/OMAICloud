from __future__ import annotations
from typing import Any

STATES = [
    "LISTENING", "CURIOUS", "THINKING", "FOCUSED",
    "EXPLAINING", "HAPPY", "CONCERNED", "WAITING",
]

class EmotionContext:
    def map_mode(self, presence_mode: str) -> str:
        m = (presence_mode or "idle").lower()
        table = {
            "attentive": "LISTENING",
            "silent_listening": "LISTENING",
            "thinking": "THINKING",
            "remembering": "THINKING",
            "speaking": "EXPLAINING",
            "concerned": "CONCERNED",
            "excited": "HAPPY",
            "focused": "FOCUSED",
            "waiting": "WAITING",
            "curious": "CURIOUS",
        }
        return table.get(m, "WAITING")

    def to_dict(self, presence_mode: str = "idle") -> dict[str, Any]:
        return {"state": self.map_mode(presence_mode), "states": STATES}
