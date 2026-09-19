"""Voice provider facade — macOS say today, neural adapters tomorrow."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .neural_tts import NeuralTTS
from .prosody_controller import ProsodyController
from .speech_stream import SpeechStream
from .voice_emotion import VoiceEmotion
from .voice_clone_adapter import VoiceCloneAdapter

_ENGINE = None


class VoiceProvider:
    def __init__(self) -> None:
        self.prosody = ProsodyController()
        self.emotion = VoiceEmotion()
        self.neural = NeuralTTS()
        self.stream = SpeechStream()
        self.clone = VoiceCloneAdapter()
        self._fallback = None

    def _synth(self):
        if self._fallback is None:
            from om_ai.core.voice_intelligence.speech_synthesizer import SpeechSynthesizer
            self._fallback = SpeechSynthesizer()
        return self._fallback

    def status(self) -> dict[str, Any]:
        s = self._synth().status()
        return {
            "ready": True,
            "step": 53,
            "name": "Neural Voice Engine",
            "backend": s.get("backend"),
            "voice": s.get("voice"),
            "rate": s.get("rate"),
            "neural": self.neural.status(),
            "clone": self.clone.status(),
        }

    def speak_plan(self, text: str, *, emotion: str = "calm", presence: str = "speaking") -> dict[str, Any]:
        styled = self.emotion.apply(text, emotion=emotion)
        paced = self.prosody.apply(styled, presence=presence)
        return {"text": paced, "emotion": emotion, "presence": presence, "streamable": True}

    def synthesize(self, text: str, *, output_path: str | Path | None = None, emotion: str = "calm", presence: str = "speaking") -> dict[str, Any]:
        plan = self.speak_plan(text, emotion=emotion, presence=presence)
        # Prefer neural if configured; else macOS say via SpeechSynthesizer
        neural = self.neural.synthesize(plan["text"], output_path=output_path)
        if neural.get("ok"):
            return {**neural, "plan": plan, "provider": "neural"}
        out = self._synth().synthesize(plan["text"], output_path=output_path)
        return {**out, "plan": plan, "provider": out.get("backend")}


def get_voice_engine() -> VoiceProvider:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = VoiceProvider()
    return _ENGINE
