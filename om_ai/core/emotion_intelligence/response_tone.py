"""Response tone from emotion + need."""
from __future__ import annotations

from typing import Any


class ResponseTone:
    def select(self, emotion: str, *, need: str = "steady") -> dict[str, Any]:
        e = (emotion or "neutral").lower()
        if need == "listen_first" or e in {"stressed", "sad", "masked_stress", "tired"}:
            return {"response_style": "supportive", "tone": "soft", "max_sentences": 2}
        if e in {"frustrated", "urgent"}:
            return {"response_style": "supportive", "tone": "calm_focused", "max_sentences": 2}
        if e in {"happy", "excited"}:
            return {"response_style": "warm_share", "tone": "warm", "max_sentences": 2}
        return {"response_style": "balanced", "tone": "calm", "max_sentences": 3}
