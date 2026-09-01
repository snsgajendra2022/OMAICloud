"""Emotion / experience style helpers for OM chat."""
from __future__ import annotations

import random

EXPERIENCE_PHASES = (
    "Thinking…",
    "Checking context…",
    "Creating architecture…",
    "Here is the solution…",
)

_OPENERS_GREETING = (
    "Hey — good to see you.",
    "Hello!",
    "Hey there.",
)
_OPENERS_GENERAL = (
    "Got it.",
    "I understand what you need.",
    "Let's dig in.",
    "Here's the clear take.",
)


def style_opening(*, intent: str = "chat", user_text: str = "") -> str:
    t = (user_text or "").lower()
    if intent == "greeting" or any(w in t for w in ("hi", "hello", "hey", "namaste")):
        return random.choice(_OPENERS_GREETING)
    return random.choice(_OPENERS_GENERAL)
