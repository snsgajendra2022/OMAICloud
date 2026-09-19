"""Emotion signals for voice style — not canned conversation replies."""
from __future__ import annotations

import re


class EmotionDetector:
    """Detect affective tone from user speech for TTS / style adaptation only."""

    _PATTERNS: list[tuple[str, re.Pattern[str]]] = [
        ("stress", re.compile(r"(?i)\b(stress|tension|pressure|overwhelmed|anxious|परेशान)\b")),
        ("sad", re.compile(r"(?i)\b(sad|alone|hurt|lonely|down|उदास)\b")),
        ("happy", re.compile(r"(?i)\b(happy|great|awesome|excited|mast|खुश)\b")),
        ("tired", re.compile(r"(?i)\b(tired|exhausted|burned?\s*out|thak|thaka|थक)\b")),
        ("curious", re.compile(r"(?i)\b(why|how|what if|explain|samjhao)\b")),
    ]

    def detect(self, text: str) -> str:
        t = text or ""
        for label, pat in self._PATTERNS:
            if pat.search(t):
                return label
        return "neutral"
