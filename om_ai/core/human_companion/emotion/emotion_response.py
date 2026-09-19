"""Emotion → response guidance."""
from __future__ import annotations

from typing import Any


_GUIDE = {
    "frustration": "Acknowledge the friction briefly, stay calm, offer a concrete next step. No pep-talk fluff.",
    "urgency": "Be concise and action-first. Skip small talk.",
    "stress": "Soften tone. One clear step at a time.",
    "sad": "Warm and steady. Don't over-ask.",
    "excitement": "Match energy lightly. Keep it sharp.",
    "happy": "Warm and brief.",
    "tired": "Shorter replies. Reduce cognitive load.",
    "curious": "Explain clearly in plain language.",
    "neutral": "Natural companion tone.",
}


class EmotionResponse:
    def guide(self, emotion: dict[str, Any] | str) -> dict[str, Any]:
        if isinstance(emotion, dict):
            label = str(emotion.get("label") or emotion.get("emotion") or "neutral")
        else:
            label = str(emotion or "neutral")
        return {
            "label": label,
            "guidance": _GUIDE.get(label, _GUIDE["neutral"]),
            "tts_emotion": {
                "frustration": "soft",
                "stress": "soft",
                "sad": "soft",
                "urgency": "focused",
                "excitement": "excited",
                "happy": "warm",
                "tired": "soft",
            }.get(label, "calm"),
        }
