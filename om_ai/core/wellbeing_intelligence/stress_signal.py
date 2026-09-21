"""Stress / overload conversational signals."""
from __future__ import annotations

import re
from typing import Any


class StressSignal:
    _STRESS = re.compile(
        r"(?i)\b(stress|stressed|anxious|tension|pareshaan|pressure|"
        r"overwhelmed|too much work|drowning|non[- ]stop)\b"
    )
    _LOW = re.compile(r"(?i)\b(hopeless|empty|nothing matters|very down)\b")

    def detect(self, message: str) -> dict[str, Any]:
        text = message or ""
        if self._LOW.search(text):
            return {
                "signal": "low_mood",
                "confidence": 0.75,
                "label": "negative mood",
                "hit": True,
            }
        if self._STRESS.search(text):
            return {
                "signal": "stress_load",
                "confidence": 0.8,
                "label": "stress signals",
                "hit": True,
            }
        return {"signal": None, "confidence": 0.0, "label": None, "hit": False}
