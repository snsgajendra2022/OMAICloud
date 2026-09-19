"""Compat shims — prefer om_ai.core.voice_engine."""
from __future__ import annotations

from om_ai.core.voice_engine.emotion_voice import EmotionVoice
from om_ai.core.voice_engine.streaming_voice import StreamingVoice
from om_ai.core.voice_engine.voice_profiles import VoiceProfiles


class TTSEngine:
    def synthesize(self, text: str, *, emotion: str = "calm"):
        try:
            from om_ai.core.voice_engine import get_voice_engine

            return get_voice_engine().synthesize(text, emotion=emotion)
        except Exception as exc:
            return {"ok": False, "reason": str(exc), "fallback": "system_say"}


__all__ = ["EmotionVoice", "StreamingVoice", "VoiceProfiles", "TTSEngine"]
