"""Conversation-level audio state for barge-in and continuous listen."""
from __future__ import annotations

from typing import Any

from .audio_processor import AudioProcessor
from .noise_reduction import NoiseReduction
from .speaker_detector import SpeakerDetector
from .voice_activity import VoiceActivity
from .audio_quality import AudioQuality


class ConversationAudio:
    def __init__(self) -> None:
        self.processor = AudioProcessor()
        self.noise = NoiseReduction()
        self.vad = VoiceActivity()
        self.speaker = SpeakerDetector()
        self.quality = AudioQuality()
        self.om_speaking = False

    def set_om_speaking(self, speaking: bool) -> None:
        self.om_speaking = bool(speaking)

    def observe(self, *, rms: float = 0.0, speech_prob: float = 0.0) -> dict[str, Any]:
        frame = self.processor.process(rms=rms, speech_prob=speech_prob)
        gate = self.noise.gate(energy=frame["energy"], speech_prob=frame["speech_prob"])
        vad = self.vad.update(energy=frame["energy"], speech_prob=frame["speech_prob"])
        spk = self.speaker.detect(energy=frame["energy"], speech_prob=frame["speech_prob"])
        qual = self.quality.score(
            energy=frame["energy"],
            speech_prob=frame["speech_prob"],
            noise_reject=bool(gate.get("reject_as_noise")),
        )
        barge = bool(self.om_speaking and vad.get("speaking") and qual.get("trust_transcript"))
        return {
            "frame": frame,
            "noise": gate,
            "vad": vad,
            "speaker": spk,
            "quality": qual,
            "barge_in": barge,
            "om_speaking": self.om_speaking,
        }
