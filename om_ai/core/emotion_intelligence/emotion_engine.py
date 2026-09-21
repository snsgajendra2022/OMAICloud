"""Emotion engine — full affect pack for a turn."""
from __future__ import annotations

from typing import Any

from .emotion_detector import EmotionDetector
from .emotional_context import EmotionalContext
from .empathy_engine import EmpathyEngine
from .mood_tracker import MoodTracker
from .response_tone import ResponseTone


class EmotionEngine:
    def __init__(self) -> None:
        self.detector = EmotionDetector()
        self.mood = MoodTracker()
        self.empathy = EmpathyEngine()
        self.tone = ResponseTone()
        self.context = EmotionalContext()

    def analyze(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        listen_first_hint: bool = False,
    ) -> dict[str, Any]:
        det = self.detector.detect(
            message,
            history=history,
            prior_mood=str(self.mood.mood),
        )
        emotion = str(det.get("emotion") or "neutral")
        mood = self.mood.update(emotion)

        need = "steady"
        if listen_first_hint or emotion in {
            "stressed",
            "sad",
            "tired",
            "fatigue",
            "masked_stress",
            "frustrated",
            "confused",
        }:
            need = "listen_first"
        if emotion in {"tired", "fatigue"}:
            need = "support_and_listen"
        if emotion in {"happy", "excited"}:
            need = "share"

        tone = self.tone.select(
            "tired" if emotion == "fatigue" else emotion,
            need="listen_first" if need == "support_and_listen" else need,
        )
        if need == "support_and_listen":
            tone = {**tone, "response_style": "supportive", "tone": "warm"}
        empathy = self.empathy.guide(
            "tired" if emotion == "fatigue" else emotion,
            need="listen_first" if need == "support_and_listen" else need,
        )

        pack = {
            "emotion": emotion,
            "label": emotion,
            "confidence": float(det.get("confidence") or 0.55),
            "response_style": tone["response_style"],
            "need": need,
            "tone": tone.get("tone"),
            "followup_required": need in {"listen_first", "support_and_listen"},
            "max_sentences": tone.get("max_sentences"),
            "masked": bool(det.get("masked")),
            "mood": mood,
            "empathy": empathy,
            "context": self.context.summary(),
            "source": det.get("source"),
        }
        self.context.push(pack)
        return pack
