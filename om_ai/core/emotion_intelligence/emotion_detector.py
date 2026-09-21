"""Emotion detector with surface + masked-affect signals."""
from __future__ import annotations

import re
from typing import Any


class EmotionDetector:
    _RULES: list[tuple[str, float, re.Pattern[str]]] = [
        ("frustrated", 0.9, re.compile(r"(?i)\b(frustrat\w*|annoying|irritat\w*|gussa|not working|still broken)\b")),
        ("stressed", 0.88, re.compile(r"(?i)\b(stress|anxious|overwhelmed|pressure|pareshaan|tension|too much)\b")),
        ("tired", 0.86, re.compile(r"(?i)\b((?:very\s+)?tired|exhausted|thak|burn(?:ed)?\s*out|no sleep|slept only)\b")),
        ("confused", 0.84, re.compile(r"(?i)\b(confus\w*|don't understand|samajh\s+nahi|not sure what|unclear)\b")),
        ("sad", 0.84, re.compile(r"(?i)\b(sad|upset|lonely|down|udas|rough day|difficult)\b")),
        ("happy", 0.85, re.compile(r"(?i)\b(happy|great|excited|fixed|finally|awesome|mast)\b")),
        ("urgent", 0.88, re.compile(r"(?i)\b(urgent|asap|right now|jaldi|immediately)\b")),
        ("excited", 0.86, re.compile(r"(?i)\b(excited|let'?s go|pumped|zabardast)\b")),
    ]

    _MASKING = re.compile(r"(?i)\b(i'?m\s+(?:fine|okay|ok)|i\s+am\s+(?:fine|okay)|theek\s+hoon)\b")

    def detect(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        prior_mood: str = "neutral",
    ) -> dict[str, Any]:
        t = text or ""
        low = t.lower()
        hist = history or []

        for label, conf, pat in self._RULES:
            if pat.search(t):
                return {
                    "emotion": label,
                    "confidence": conf,
                    "source": "lexicon",
                    "masked": False,
                }

        if self._MASKING.search(low):
            # "I am okay" after stress / with short curt tone → possible masking
            prior_stress = prior_mood in {"stressed", "frustrated", "sad", "tired"}
            recent_heavy = any(
                re.search(r"(?i)\b(stress|tired|difficult|problem|fail)\b", str(h.get("content") or h.get("text") or ""))
                for h in hist[-4:]
            )
            if prior_stress or recent_heavy or len(low.split()) <= 4:
                return {
                    "emotion": "masked_stress",
                    "confidence": 0.62,
                    "source": "context",
                    "masked": True,
                    "surface": "okay",
                }

        return {
            "emotion": "neutral",
            "confidence": 0.55,
            "source": "default",
            "masked": False,
        }
