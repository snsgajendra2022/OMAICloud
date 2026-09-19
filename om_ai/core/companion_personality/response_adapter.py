"""Adapt brain responses for voice without replacing conversational intelligence."""
from __future__ import annotations

from typing import Any

from .speech_style import SpeechStyle


class ResponseAdapter:
    """Last-mile adapter: brain text → spoken + TTS plan."""

    def __init__(self) -> None:
        self.style = SpeechStyle()

    def adapt(
        self,
        response: str,
        *,
        locale: str = "en",
        emotion: str = "neutral",
        personality: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spoken = self.style.transform(
            response=response,
            locale=locale,
            emotion=emotion,
            personality=personality,
        )
        return {
            "spoken": spoken,
            "spoken_tts": self.style.pace_for_tts(spoken),
            "display": (response or "").strip() or spoken,
            "locale": locale,
            "emotion": emotion,
            "trimmed": len((response or "").split()) > len(spoken.split()) + 5,
        }
