"""Voice + timing subsystem for human companion."""
from __future__ import annotations

from typing import Any

from .breathing_engine import BreathingEngine
from .emotion_voice import EmotionVoice
from .noise_filter import NoiseFilter
from .pause_controller import PauseController
from .prosody_engine import ProsodyEngine
from .speech_timing import SpeechTiming
from .wake_word import WakeWord


class VoiceSubsystem:
    def __init__(self) -> None:
        self.wake = WakeWord()
        self.noise = NoiseFilter()
        self.timing = SpeechTiming()
        self.breathing = BreathingEngine()
        self.pauses = PauseController()
        self.prosody = ProsodyEngine()
        self.emotion_voice = EmotionVoice()

    def prepare_delivery(self, text: str, *, emotion: str = "calm") -> dict[str, Any]:
        timed = self.timing.apply(text, emotion=emotion)
        paused = self.pauses.apply(timed["spoken"], emotion=emotion)
        prosody = self.prosody.plan(paused, emotion=emotion)
        breath = self.breathing.markers(paused)
        ev = self.emotion_voice.map(emotion)
        return {
            "spoken": paused,
            "spoken_tts": paused,
            "rate": prosody.get("rate") or ev.get("rate") or 178,
            "emotion": ev.get("tts_emotion") or emotion,
            "timing": timed,
            "prosody": prosody,
            "breathing": breath,
        }
