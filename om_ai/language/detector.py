"""Detect user language (script + langdetect fallback)."""
from __future__ import annotations

import re


class LanguageDetector:
    def detect(self, text: str) -> str:
        t = (text or "").strip()
        if not t:
            return "en"
        # Script-first (reliable offline)
        if re.search(r"[\u0900-\u097F]", t):
            return "hi"
        if re.search(r"[\u0600-\u06FF]", t):
            return "ar"
        if re.search(r"[\u0A80-\u0AFF]", t):
            return "gu"
        if re.search(r"[\u0B80-\u0BFF]", t):
            return "ta"
        if re.search(r"[\u0C00-\u0C7F]", t):
            return "te"
        if re.search(r"[\u4E00-\u9FFF]", t):
            return "zh"
        try:
            from langdetect import detect

            lang = detect(t)
            return str(lang or "en")[:8] or "en"
        except Exception:
            return "en"
