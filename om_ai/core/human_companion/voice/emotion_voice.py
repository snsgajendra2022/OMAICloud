"""Emotion → TTS voice mapping."""
from __future__ import annotations

from typing import Any


class EmotionVoice:
    def map(self, emotion: str) -> dict[str, Any]:
        e = (emotion or "calm").lower()
        table = {
            "soft": {"tts_emotion": "soft", "rate": 162},
            "concerned": {"tts_emotion": "soft", "rate": 162},
            "excited": {"tts_emotion": "excited", "rate": 188},
            "warm": {"tts_emotion": "calm", "rate": 176},
            "focused": {"tts_emotion": "calm", "rate": 174},
            "frustration": {"tts_emotion": "soft", "rate": 165},
            "stress": {"tts_emotion": "soft", "rate": 162},
            "urgency": {"tts_emotion": "focused", "rate": 182},
            "happy": {"tts_emotion": "warm", "rate": 180},
            "sad": {"tts_emotion": "soft", "rate": 160},
        }
        return table.get(e, {"tts_emotion": "calm", "rate": 178})
