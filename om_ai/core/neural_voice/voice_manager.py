from __future__ import annotations
from typing import Any

from .emotion_voice import EmotionVoice
from .interruption_voice import InterruptionVoice
from .streaming_voice import StreamingVoice
from .tts_engine import TTSEngine
from .voice_profiles import VoiceProfiles

_RT = None

class NeuralVoiceRuntime:
    def __init__(self) -> None:
        self.profiles = VoiceProfiles()
        self.tts = TTSEngine()
        self.emotion = EmotionVoice()
        self.stream = StreamingVoice()
        self.interrupt = InterruptionVoice()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 105, "profile": self.profiles.get()}

    def speak_plan(self, text: str, *, emotion: str = "calm") -> dict[str, Any]:
        # Prefer existing voice_engine pacing
        try:
            from om_ai.core.voice_engine import get_voice_engine
            return get_voice_engine().speak_plan(text, emotion=emotion)
        except Exception:
            return {"text": text, "emotion": self.emotion.map(emotion), "tts": self.tts.synthesize(text, emotion=emotion)}

def get_neural_voice() -> NeuralVoiceRuntime:
    global _RT
    if _RT is None:
        _RT = NeuralVoiceRuntime()
    return _RT
