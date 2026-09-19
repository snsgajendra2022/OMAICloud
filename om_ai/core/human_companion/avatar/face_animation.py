from typing import Any


class FaceAnimation:
    def for_emotion(self, emotion: str) -> dict[str, Any]:
        return {"mood": emotion or "neutral", "brow": 0.1 if emotion in {"stress", "frustration"} else 0.0}
