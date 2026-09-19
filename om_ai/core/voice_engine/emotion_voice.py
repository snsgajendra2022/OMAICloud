"""STEP 3 — Emotional delivery shaping for spoken replies (Aman / human male)."""
from __future__ import annotations

import re
from typing import Any


class EmotionVoice:
    """Maps emotion labels → delivery knobs + light text shaping."""

    def map(self, emotion: str) -> dict[str, Any]:
        e = (emotion or "calm").lower()
        table = {
            "concerned": {
                "stability": 0.68,
                "style": 0.38,
                "rate": 0.94,
                "volume": 0.9,
                "similarity": 0.8,
                "wpm": 168,
            },
            "excited": {
                "stability": 0.42,
                "style": 0.65,
                "rate": 1.06,
                "volume": 1.0,
                "similarity": 0.72,
                "wpm": 188,
            },
            "calm": {
                "stability": 0.58,
                "style": 0.42,
                "rate": 1.0,
                "volume": 0.96,
                "similarity": 0.82,
                "wpm": 178,
            },
            "soft": {
                "stability": 0.7,
                "style": 0.28,
                "rate": 0.91,
                "volume": 0.82,
                "similarity": 0.84,
                "wpm": 162,
            },
            "whisper": {
                "stability": 0.78,
                "style": 0.18,
                "rate": 0.88,
                "volume": 0.4,
                "similarity": 0.86,
                "wpm": 158,
            },
            "focused": {
                "stability": 0.72,
                "style": 0.3,
                "rate": 0.98,
                "volume": 0.96,
                "similarity": 0.8,
                "wpm": 174,
            },
            "happy": {
                "stability": 0.48,
                "style": 0.55,
                "rate": 1.04,
                "volume": 1.0,
                "similarity": 0.75,
                "wpm": 184,
            },
            "tired": {
                "stability": 0.74,
                "style": 0.22,
                "rate": 0.9,
                "volume": 0.85,
                "similarity": 0.83,
                "wpm": 160,
            },
        }
        return table.get(e, table["calm"])

    def apply(self, text: str, *, emotion: str = "calm") -> str:
        t = (text or "").strip()
        if not t:
            return t
        e = (emotion or "calm").lower()
        knobs = self.map(e)
        # Volume markers only when meaningfully soft — avoid dulling Aman
        if e == "whisper":
            t = f"[[volm {knobs['volume']}]] {t}"
        elif e in {"soft", "tired"} and knobs["volume"] < 0.9:
            t = f"[[volm {knobs['volume']}]] {t}"
        if e == "excited" and t.endswith("."):
            t = t[:-1] + "!"
        return t

    def playback_rate(self, emotion: str = "calm") -> float:
        """Browser playback hint — keep near 1.0 so Aman stays clear."""
        return float(self.map(emotion).get("rate") or 1.0)


# Back-compat alias
VoiceEmotion = EmotionVoice
