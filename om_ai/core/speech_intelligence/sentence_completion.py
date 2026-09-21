"""Detect whether the spoken thought is complete enough to answer."""
from __future__ import annotations

import re
from typing import Any


# Structural incompleteness — connectors / open clauses, not FAQ keywords
_TRAILING_OPEN = re.compile(
    r"(?i)("
    r"\.\.\.|…|"
    r"\b(and|but|so|because|then|or|if|when|while|though|although|"
    r"aur|lekin|kyunki|phir|toh|to|ki|ke|ka|mein|me|se|par|pe)\s*$|"
    r"[,;:]\s*$"
    r")"
)

_COMPLETE_MARKERS = re.compile(
    r"(?i)(\?|!|"
    r"\b(please|thanks|thank you|ok|okay|yes|no|haan|nahi|theek|"
    r"open|search|check|analyze|prepare|stop|cancel)\b)"
)


class SentenceCompletion:
    def assess(self, text: str) -> dict[str, Any]:
        t = (text or "").strip()
        if not t:
            return {
                "complete": False,
                "confidence": 0.95,
                "reason": "empty",
                "should_wait": True,
            }
        words = re.findall(r"[A-Za-z\u0900-\u097F']+", t)
        trailing_open = bool(_TRAILING_OPEN.search(t))
        # Truncated mid-thought: ends mid-phrase without terminal punctuation
        ends_soft = not t.endswith((".", "?", "!", "।"))
        short_fragment = len(words) <= 4 and ends_soft and not _COMPLETE_MARKERS.search(t)
        # "OM I was thinking about my project and..."
        open_conjunction = bool(
            re.search(
                r"(?i)\b(and|but|so|because|aur|lekin|kyunki|toh)\s*$",
                t,
            )
        )
        incomplete = trailing_open or open_conjunction or short_fragment
        # Clear command / question → complete enough
        if _COMPLETE_MARKERS.search(t) and not open_conjunction and len(words) >= 2:
            incomplete = False
        conf = 0.82 if incomplete else (0.75 if ends_soft and len(words) < 6 else 0.7)
        return {
            "complete": not incomplete,
            "confidence": conf,
            "reason": (
                "trailing_open"
                if trailing_open or open_conjunction
                else ("short_fragment" if short_fragment else "utterance_ok")
            ),
            "should_wait": incomplete,
            "word_count": len(words),
        }
