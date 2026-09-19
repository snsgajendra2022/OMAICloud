"""Emotion subsystem."""
from __future__ import annotations

from typing import Any

from .emotion_detector import EmotionDetector
from .emotion_response import EmotionResponse
from .mood_tracker import MoodTracker
from .relationship_state import RelationshipState


class EmotionSystem:
    def __init__(self) -> None:
        self.detector = EmotionDetector()
        self.mood = MoodTracker()
        self.response = EmotionResponse()
        self.relationship = RelationshipState()

    def analyze(self, text: str) -> dict[str, Any]:
        det = self.detector.detect(text)
        mood = self.mood.update(det["label"])
        guide = self.response.guide(det)
        rel = self.relationship.observe(emotion=det["label"])
        return {**det, "mood": mood, "response_guide": guide, "relationship": rel}
