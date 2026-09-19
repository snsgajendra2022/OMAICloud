from __future__ import annotations
from typing import Any
from .emotion_context import EmotionContext
from .tone_controller import ToneController
from .response_mood import ResponseMood

class ExpressionEngine:
    def __init__(self) -> None:
        self.emotion = EmotionContext()
        self.tone = ToneController()
        self.mood = ResponseMood()

    def express(self, presence_mode: str) -> dict[str, Any]:
        state = self.emotion.map_mode(presence_mode)
        return {
            "state": state,
            "mood": self.mood.label(state),
            "tone": self.tone.for_state(state),
            "avatar_hint": state.lower(),
        }
