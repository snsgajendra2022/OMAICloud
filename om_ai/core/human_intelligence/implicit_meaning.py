"""Implicit meaning — infer stress / need / unspoken situation."""
from __future__ import annotations

import re
from typing import Any


class ImplicitMeaning:
    """
    User: "Today was very difficult"
    Not: "What is difficult?"
    Understand: stress / frustration / tiredness / a problem → listen first.
    """

    _PATTERNS: list[tuple[re.Pattern[str], list[str], str, str]] = [
        (
            re.compile(
                r"(?i)\b(today was|day was|rough day|hard day|difficult|"
                r"tough day|bad day|hectic|long day)\b"
            ),
            ["stress", "frustration", "tiredness", "problem"],
            "rough_day",
            "It sounds like you had a rough day. What happened?",
        ),
        (
            re.compile(r"(?i)\b(i'?m\s+fine|i\s+am\s+fine|i'?m\s+okay|i\s+am\s+okay|theek\s+hoon)\b"),
            ["possible_masking", "stress"],
            "maybe_masking",
            "You say you're okay — I'm here if something's weighing on you.",
        ),
        (
            re.compile(r"(?i)\b(fixed the bug|i fixed|it works|finally worked|solved it)\b"),
            ["relief", "pride", "closure"],
            "win",
            "Nice! That bug was probably annoying. What was causing the issue?",
        ),
        (
            re.compile(r"(?i)\b((?:i am|i'?m|feeling)\s+(?:very\s+)?tired|thak)\b"),
            ["fatigue", "need_support"],
            "fatigue",
            "You sound really tired today. Was it because of work, stress, or something else?",
        ),
        (
            re.compile(r"(?i)\b(can'?t sleep|couldn'?t sleep|no sleep|slept only|insomnia)\b"),
            ["fatigue", "stress", "health_signal"],
            "sleep_strain",
            "That sounds exhausting. How are you feeling right now?",
        ),
        (
            re.compile(r"(?i)\b(overwhelmed|too much|drowning|burn(?:ed)?\s*out)\b"),
            ["stress", "overload", "need_support"],
            "overload",
            "Sounds like a lot at once. Want to unpack one piece together?",
        ),
    ]

    def infer(
        self,
        message: str,
        *,
        conversation: dict[str, Any] | None = None,
        emotion: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = message or ""
        low = text.lower()
        conversation = conversation or {}
        emotion = emotion or {}

        for pat, possibles, label, ask in self._PATTERNS:
            if pat.search(low):
                return {
                    "has_implicit": True,
                    "label": label,
                    "possible": possibles,
                    "natural_ask": ask,
                    "listen_first": label in {"rough_day", "maybe_masking", "sleep_strain", "overload"},
                    "source": "pattern",
                }

        # Soft inference from analyzer + emotion without a hard phrase match
        if conversation.get("venting") or emotion.get("label") in {
            "stress",
            "frustration",
            "sad",
            "tired",
        }:
            return {
                "has_implicit": True,
                "label": "emotional_load",
                "possible": [str(emotion.get("label") or "stress"), "need_to_be_heard"],
                "natural_ask": "I'm listening. What felt hardest about it?",
                "listen_first": True,
                "source": "affect",
            }

        return {
            "has_implicit": False,
            "label": "none",
            "possible": [],
            "natural_ask": None,
            "listen_first": False,
            "source": "none",
        }
