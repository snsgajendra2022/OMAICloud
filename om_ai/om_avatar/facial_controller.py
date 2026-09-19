from __future__ import annotations
from typing import Any

class FacialController:
    def for_mood(self, mood: str) -> dict[str, Any]:
        m = (mood or "neutral").lower()
        brows = {"concerned": 0.6, "happy": -0.2, "thinking": 0.3}.get(m, 0.0)
        return {"brows": brows, "smile": 0.4 if m == "happy" else 0.1, "mood": m}
