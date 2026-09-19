from __future__ import annotations

class EmotionVoice:
    def map(self, emotion: str) -> dict:
        e = (emotion or "calm").lower()
        table = {
            "concerned": {"stability": 0.7, "style": 0.35, "rate": 0.88},
            "excited": {"stability": 0.4, "style": 0.7, "rate": 1.02},
            "calm": {"stability": 0.55, "style": 0.45, "rate": 0.92},
        }
        return table.get(e, table["calm"])
