"""Emotion meaning engine — affect meaning for a turn (alias + helper)."""
from __future__ import annotations

from typing import Any

from om_ai.core.emotion_intelligence.emotion_detector import EmotionDetector
from om_ai.core.emotion_intelligence.empathy_engine import EmpathyEngine


class EmotionMeaningEngine:
    def __init__(self) -> None:
        self.detector = EmotionDetector()
        self.empathy = EmpathyEngine()

    def analyze(self, message: str, *, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        det = self.detector.detect(message, history=history)
        guide = self.empathy.guide(str(det.get("emotion") or "neutral"))
        return {
            "emotion": det.get("emotion"),
            "confidence": det.get("confidence"),
            "response": guide.get("response"),
            "ack_line": guide.get("ack_line"),
            "empathy_move": guide.get("empathy_move"),
            "om_claims_feelings": False,
        }
