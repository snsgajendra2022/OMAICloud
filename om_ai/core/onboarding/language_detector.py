"""Detect preferred language from onboarding profile / free text."""
from __future__ import annotations

import re
from typing import Any


_DEV = re.compile(r"[\u0900-\u097F]")
_HING = re.compile(
    r"(?i)\b(hai|hain|kya|nahi|theek|bhai|yaar|kal|aaj|mujhe|karna|hinglish)\b"
)


class LanguageDetector:
    def detect(self, profile: dict[str, Any] | None = None, text: str = "") -> str:
        raw = str((profile or {}).get("language") or "").strip().lower()
        if raw in {"en", "english"}:
            return "en"
        if raw in {"hi", "hindi"}:
            return "hi"
        if raw in {"hi-en", "hinglish", "hi_en"}:
            return "hi-en"
        if raw and raw != "auto":
            return raw

        blob = " ".join(
            str((profile or {}).get(k) or "")
            for k in ("purpose", "style", "notes", "display_name")
        )
        blob = f"{blob} {text}".strip()
        if _DEV.search(blob) and re.search(r"[A-Za-z]", blob):
            return "hi-en"
        if _DEV.search(blob):
            return "hi"
        if _HING.search(blob):
            return "hi-en"
        return "en"
