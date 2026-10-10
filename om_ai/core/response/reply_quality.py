"""
Dependency-free reply quality utilities.

This module intentionally contains no imports from:
    - agents
    - cognitive brain
    - chat orchestrator
    - production brain
    - API
    - model runtime

It must remain safe to import from any layer.
"""

from __future__ import annotations

import re


_STATIC_REPLIES = {
    "hello",
    "hi",
    "hey",
    "ok",
    "okay",
    "i understand",
    "i'm here",
    "i am here",
    "tell me what you want",
    "please provide more details",
}


def is_low_quality_reply(
    text: str | None,
) -> bool:
    """
    Detect obviously unusable or corrupted model replies.

    This function does not judge factual correctness.
    It only detects structural/quality failures.
    """

    value = str(text or "").strip()

    # ---------------------------------------------------------
    # Empty response
    # ---------------------------------------------------------

    if not value:
        return True

    lowered = value.lower()

    # ---------------------------------------------------------
    # Unicode replacement character
    # ---------------------------------------------------------

    if "\ufffd" in value:
        return True

    # ---------------------------------------------------------
    # Null bytes
    # ---------------------------------------------------------

    if "\x00" in value:
        return True

    # ---------------------------------------------------------
    # Control-character corruption
    # ---------------------------------------------------------

    control_count = sum(
        1
        for char in value
        if ord(char) < 32
        and char not in "\n\r\t"
    )

    if control_count > 2:
        return True

    # ---------------------------------------------------------
    # Extremely short output
    # ---------------------------------------------------------

    if len(value) <= 1:
        return True

    # ---------------------------------------------------------
    # Known static fallback responses
    # ---------------------------------------------------------

    if lowered in _STATIC_REPLIES:
        return True

    # ---------------------------------------------------------
    # Token repetition detection
    # ---------------------------------------------------------

    words = re.findall(
        r"\b[\w'-]+\b",
        lowered,
    )

    if len(words) >= 12:

        unique_ratio = (
            len(set(words))
            / max(len(words), 1)
        )

        if unique_ratio < 0.20:
            return True

    # ---------------------------------------------------------
    # Long-output corruption detection
    # ---------------------------------------------------------

    if len(value) > 200:

        alpha_count = sum(
            1
            for char in value
            if char.isalpha()
        )

        printable_count = sum(
            1
            for char in value
            if char.isprintable()
        )

        alpha_ratio = (
            alpha_count
            / max(len(value), 1)
        )

        printable_ratio = (
            printable_count
            / max(len(value), 1)
        )

        if alpha_ratio < 0.15:
            return True

        if printable_ratio < 0.85:
            return True

    return False