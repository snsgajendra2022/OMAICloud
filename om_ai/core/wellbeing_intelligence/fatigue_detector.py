"""Fatigue / sleep-debt conversational signals."""
from __future__ import annotations

import re
from typing import Any


class FatigueDetector:
    _SLEEP = re.compile(
        r"(?i)\b("
        r"slept only|only\s+\d+\s+hours?(?:\s+(?:of\s+)?sleep)?|"
        r"(?:every|each)\s+day\s+this\s+week|"
        r"for\s+(?:the\s+)?last\s+week|all\s+week|"
        r"no sleep|insomnia|can'?t sleep|couldn'?t sleep|"
        r"\d+\s+hours?\s+(?:sleep|a\s+night)"
        r")\b"
    )
    _TIRED = re.compile(
        r"(?i)\b(very tired|exhausted|worn out|drained|thak(?:a| gaya)?|"
        r"burn(?:ed)?\s*out|no energy)\b"
    )

    def detect(self, message: str) -> dict[str, Any]:
        text = message or ""
        if self._SLEEP.search(text):
            return {
                "signal": "sleep_deprivation",
                "confidence": 0.82,
                "label": "sleep problems",
                "hit": True,
            }
        if self._TIRED.search(text):
            return {
                "signal": "fatigue",
                "confidence": 0.78,
                "label": "fatigue",
                "hit": True,
            }
        return {"signal": None, "confidence": 0.0, "label": None, "hit": False}
