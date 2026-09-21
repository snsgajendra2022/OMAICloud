"""Normalize and score raw listening frames (browser or native)."""
from __future__ import annotations

from typing import Any


class AudioProcessor:
    def process(
        self,
        *,
        rms: float = 0.0,
        speech_prob: float = 0.0,
        sample_rate: int = 16000,
    ) -> dict[str, Any]:
        energy = max(0.0, min(1.0, float(rms)))
        speech = max(0.0, min(1.0, float(speech_prob)))
        usable = energy >= 0.02 or speech >= 0.35
        return {
            "energy": energy,
            "speech_prob": speech,
            "sample_rate": int(sample_rate or 16000),
            "usable": usable,
            "quality": "clear" if energy >= 0.08 and speech >= 0.5 else ("soft" if usable else "noise"),
        }
