"""Energy-based VAD (deterministic signal processing — not conversation intelligence)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np


@dataclass
class VADResult:
    speaking: bool
    speech_started: bool
    speech_ended: bool
    energy: float
    state: str  # silence | speech_started | speech_ongoing | speech_ended


class VoiceActivityDetector:
    def __init__(
        self,
        *,
        energy_threshold: float = 0.015,
        hangover_frames: int = 8,
        start_frames: int = 3,
    ) -> None:
        self.energy_threshold = energy_threshold
        self.hangover_frames = hangover_frames
        self.start_frames = start_frames
        self._active = False
        self._above = 0
        self._below = 0

    def reset(self) -> None:
        self._active = False
        self._above = 0
        self._below = 0

    def process(self, samples) -> VADResult:
        arr = np.asarray(samples, dtype=np.float32).reshape(-1)
        energy = float(np.sqrt(np.mean(np.square(arr)))) if arr.size else 0.0
        speech_started = False
        speech_ended = False
        if energy >= self.energy_threshold:
            self._above += 1
            self._below = 0
            if not self._active and self._above >= self.start_frames:
                self._active = True
                speech_started = True
        else:
            self._below += 1
            self._above = 0
            if self._active and self._below >= self.hangover_frames:
                self._active = False
                speech_ended = True
        if speech_started:
            state = "speech_started"
        elif speech_ended:
            state = "speech_ended"
        elif self._active:
            state = "speech_ongoing"
        else:
            state = "silence"
        return VADResult(
            speaking=self._active,
            speech_started=speech_started,
            speech_ended=speech_ended,
            energy=energy,
            state=state,
        )

    def to_dict(self, result: VADResult) -> dict[str, Any]:
        return {
            "speaking": result.speaking,
            "speech_started": result.speech_started,
            "speech_ended": result.speech_ended,
            "energy": result.energy,
            "state": result.state,
        }
