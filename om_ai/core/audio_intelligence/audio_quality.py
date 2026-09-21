"""Score listening quality for adaptive timing."""
from __future__ import annotations

from typing import Any


class AudioQuality:
    def score(self, *, energy: float = 0.0, speech_prob: float = 0.0, noise_reject: bool = False) -> dict[str, Any]:
        if noise_reject:
            return {"score": 0.1, "label": "noisy", "trust_transcript": False}
        s = 0.35 * float(energy) + 0.65 * float(speech_prob)
        label = "good" if s >= 0.55 else ("ok" if s >= 0.3 else "weak")
        return {
            "score": round(s, 3),
            "label": label,
            "trust_transcript": s >= 0.28,
        }
