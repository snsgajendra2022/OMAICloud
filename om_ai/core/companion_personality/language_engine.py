"""
OM Language Intelligence Engine

Detects reply locale and normalizes heard text for the companion path.
Optional async classifier hook for richer analysis when wired.
"""
from __future__ import annotations

import re
from typing import Any


_HI_MARKERS = re.compile(
    r"(?i)("
    r"[\u0900-\u097F]|"  # Devanagari
    r"\b(hai|hain|kya|tum|nahi|nahin|baat|ji|haan|theek|bolo|mujhe|"
    r"karo|karna|sakte|tarah|insaan|pehle|wahi|ruk|band|chup|"
    r"namaste|shukriya|dhanyavad|acha|accha|bilkul)\b"
    r")"
)

_NORM_MAP = (
    (re.compile(r"(?i)\bom\b"), "OM"),
    (re.compile(r"\s+"), " "),
)


class LanguageEngine:
    def __init__(
        self,
        classifier=None,
        memory=None,
        context=None,
    ) -> None:
        self.classifier = classifier
        self.memory = memory
        self.context = context

    def detect(self, text: str) -> str:
        """Sync locale signal for voice / personality (hi | en)."""
        t = (text or "").strip()
        if not t:
            return "en"
        if _HI_MARKERS.search(t):
            return "hi"
        return "en"

    def normalize_heard(self, text: str) -> str:
        t = (text or "").strip()
        if not t:
            return ""
        for pat, repl in _NORM_MAP:
            t = pat.sub(repl, t)
        return t.strip()

    async def analyze(
        self,
        text: str,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        analysis: dict[str, Any] = {
            "language": self.detect(text) if text else None,
            "dialect": None,
            "mixed": False,
            "confidence": 0.6 if text else 0.0,
            "response_language": None,
        }
        if not text:
            return analysis

        user_context: dict[str, Any] = {}
        if self.memory and user_id:
            user_context = await self.memory.get(user_id)

        if self.classifier:
            result = await self.classifier.predict(
                text=text,
                context={"user": user_context, "session": session_id},
            )
            if result:
                analysis.update(result)

        if self.memory and user_id and analysis.get("language"):
            await self.memory.update(
                user_id,
                {"language_preference": analysis["language"]},
            )

        analysis["response_language"] = analysis.get("language") or "en"
        return analysis

    async def response_language(self, user_id: str, detected: str) -> str:
        if self.memory:
            profile = await self.memory.get(user_id)
            preferred = profile.get("language_preference")
            if preferred:
                return preferred
        return detected or "auto"
