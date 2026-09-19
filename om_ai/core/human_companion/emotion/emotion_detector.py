"""Emotion detector — frustration, happiness, stress, excitement, urgency."""
from __future__ import annotations

import re
from typing import Any


class EmotionDetector:
    _RULES: list[tuple[str, float, re.Pattern[str]]] = [
        ("frustration", 0.92, re.compile(r"(?i)\b(frustrat\w*|annoying|irritat\w*|gussa|bakwas|nahi\s+ho\s+raha|not\s+working|still\s+broken|nothing\s+is\s+working)\b")),
        ("urgency", 0.9, re.compile(r"(?i)\b(urgent|asap|right\s+now|jaldi|abhi\s+karo|hurry|immediately)\b")),
        ("stress", 0.88, re.compile(r"(?i)\b(stress|anxious|overwhelmed|pressure|pareshaan|tension)\b")),
        ("sad", 0.85, re.compile(r"(?i)\b(sad|upset|hurt|lonely|down|udas)\b")),
        ("excitement", 0.88, re.compile(r"(?i)\b(excited|amazing|awesome|let'?s\s+go|zabardast|mast|fire)\b")),
        ("happy", 0.82, re.compile(r"(?i)\b(happy|great|thanks|shukriya|khush|good\s+job)\b")),
        ("tired", 0.8, re.compile(r"(?i)\b(tired|exhausted|thak|burn(?:ed)?\s*out)\b")),
        ("curious", 0.7, re.compile(r"(?i)\b(why|how|explain|samjhao|kya\s+hai)\b")),
    ]

    def detect(self, text: str) -> dict[str, Any]:
        t = text or ""
        for label, conf, pat in self._RULES:
            if pat.search(t):
                return {"label": label, "emotion": label, "confidence": conf, "source": "lexicon"}
        return {"label": "neutral", "emotion": "neutral", "confidence": 0.55, "source": "default"}
