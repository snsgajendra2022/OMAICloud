"""Barge-in: user speech while assistant is speaking."""
from __future__ import annotations

from typing import Any

from .voice_activity_detector import VoiceActivityDetector


class InterruptionDetector:
    def __init__(self, vad: VoiceActivityDetector | None = None) -> None:
        self.vad = vad or VoiceActivityDetector(energy_threshold=0.02, start_frames=2, hangover_frames=4)
        self.enabled = True

    def check(self, samples, *, assistant_speaking: bool) -> dict[str, Any]:
        if not self.enabled or not assistant_speaking:
            return {"interrupted": False}
        result = self.vad.process(samples)
        return {
            "interrupted": bool(result.speech_started or result.speaking),
            "vad": self.vad.to_dict(result),
        }
