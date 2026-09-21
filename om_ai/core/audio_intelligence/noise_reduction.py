"""Lightweight noise gate hints (no DSP dependency required)."""
from __future__ import annotations

from typing import Any


class NoiseReduction:
    def gate(self, *, energy: float = 0.0, speech_prob: float = 0.0) -> dict[str, Any]:
        e = float(energy or 0.0)
        s = float(speech_prob or 0.0)
        # Soft gate: treat low-energy / low-speech as background
        reject = e < 0.015 and s < 0.25
        attenuate = e < 0.04 and s < 0.4
        return {
            "reject_as_noise": reject,
            "attenuate": attenuate and not reject,
            "pass_through": not reject,
            "reason": "noise" if reject else ("soft" if attenuate else "voice"),
        }
