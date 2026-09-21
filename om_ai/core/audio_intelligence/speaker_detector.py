"""Speaker presence (single-user companion default)."""
from __future__ import annotations

from typing import Any


class SpeakerDetector:
    def detect(self, *, energy: float = 0.0, speech_prob: float = 0.0) -> dict[str, Any]:
        present = float(energy) >= 0.02 or float(speech_prob) >= 0.3
        return {
            "speaker": "user" if present else "none",
            "confidence": min(1.0, max(float(energy), float(speech_prob))),
            "multi_speaker": False,
        }
