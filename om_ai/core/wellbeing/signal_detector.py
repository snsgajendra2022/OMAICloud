"""Detect wellbeing signals without medical diagnosis."""
from __future__ import annotations

import re
from typing import Any


class SignalDetector:
    _SIGNALS: list[tuple[str, re.Pattern[str], str]] = [
        (
            "sleep_debt",
            re.compile(
                r"(?i)\b(slept only|only\s+\d+\s+hours?|no sleep|insomnia|"
                r"can'?t sleep|couldn'?t sleep|for last week|all week)\b"
            ),
            "sleep problems",
        ),
        (
            "fatigue",
            re.compile(r"(?i)\b(exhausted|worn out|drained|thak|burn(?:ed)?\s*out)\b"),
            "fatigue",
        ),
        (
            "work_overload",
            re.compile(r"(?i)\b(overwhelmed|too much work|drowning|no break|non[- ]stop)\b"),
            "work overload",
        ),
        (
            "stress_load",
            re.compile(r"(?i)\b(stress|anxious|tension|pareshaan|pressure)\b"),
            "stress signals",
        ),
        (
            "low_mood",
            re.compile(r"(?i)\b(hopeless|empty|nothing matters|very down)\b"),
            "negative mood",
        ),
    ]

    def detect(self, message: str) -> dict[str, Any]:
        hits: list[dict[str, str]] = []
        for key, pat, label in self._SIGNALS:
            if pat.search(message or ""):
                hits.append({"signal": key, "label": label})
        return {
            "has_signal": bool(hits),
            "signals": hits,
            "primary": hits[0]["signal"] if hits else None,
        }
