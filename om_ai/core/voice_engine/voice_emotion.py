"""Back-compat shim — use emotion_voice.EmotionVoice."""
from __future__ import annotations

from .emotion_voice import EmotionVoice, VoiceEmotion

__all__ = ["EmotionVoice", "VoiceEmotion"]
