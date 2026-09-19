from typing import Any


class EmotionAnimation:
    def map(self, emotion: str) -> dict[str, Any]:
        return {"label": emotion or "neutral", "presence": {
            "frustration": "concerned",
            "stress": "concerned",
            "sad": "concerned",
            "excitement": "excited",
            "happy": "attentive",
            "urgency": "attentive",
        }.get(emotion, "attentive")}
