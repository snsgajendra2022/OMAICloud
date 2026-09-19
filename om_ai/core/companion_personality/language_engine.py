"""Language detection + STT phonetic normalize for voice presence."""
from __future__ import annotations

import re


_DEVANAGARI = re.compile(r"[\u0900-\u097F]")

_HINGLISH = (
    "haan", "han", "hai", "hain", "kya", "kyu", "kyun", "bolo", "batao",
    "mujhe", "aap", "tum", "karna", "nahi", "theek", "bhai", "yaar",
    "kaise", "achha", "accha", "shukriya", "namaste",
)

# Web Speech hi-IN often writes English as Devanagari phonetics
_PHONETIC_DEV_EN = (
    (re.compile(r"व्हाट\s*आर\s*यू\s*डूइंग|व्हाट\s*आर\s*यू\s*डूइङ|व्हाट्स?\s*अप"), "what are you doing"),
    (re.compile(r"हाउ\s*आर\s*यू|हाउ\s*आर्\s*यू"), "how are you"),
    (re.compile(r"हू\s*आर\s*यू|हू\s*आर\s*यु"), "who are you"),
    (re.compile(r"व्हाट\s*आर\s*यू|वॉट\s*आर\s*यू"), "what are you"),
    (re.compile(r"गुड\s*मॉर्निंग|गुड\s*मॉरनिंग"), "good morning"),
    (re.compile(r"गुड\s*नाइट|गुड\s*नाईट"), "good night"),
    (re.compile(r"थैंक\s*यू|थैंक्स|थैङ्क\s*यू"), "thank you"),
    (re.compile(r"हैलो|हेलो|हाय|हेय"), "hello"),
    (re.compile(r"येस|यस"), "yes"),
    (re.compile(r"नो|नॉट"), "no"),
    (re.compile(r"ओके|ओ\.?के"), "ok"),
    (re.compile(r"प्लीज|प्लीज़"), "please"),
    (re.compile(r"हेल्प|हेल्‍प"), "help"),
    (re.compile(r"स्टॉप|स्टाप"), "stop"),
)


class LanguageEngine:
    def normalize_heard(self, text: str) -> str:
        """Map hi-IN phonetic English (Devanagari) back to Latin for understanding."""
        raw = (text or "").strip()
        if not raw:
            return ""
        for pat, repl in _PHONETIC_DEV_EN:
            if pat.search(raw):
                return repl
        return raw

    def detect(self, text: str) -> str:
        """Return 'hi' for Hindi/Hinglish, else 'en'."""
        if not text:
            return "en"
        normalized = self.normalize_heard(text)
        original = (text or "").strip()

        # Phonetic English → Latin → English locale
        if normalized != original and not _DEVANAGARI.search(normalized):
            return "en"

        if _DEVANAGARI.search(original):
            if any(p.search(original) for p, _ in _PHONETIC_DEV_EN):
                return "en"
            return "hi"

        low = normalized.lower()
        score = sum(1 for w in _HINGLISH if re.search(rf"\b{re.escape(w)}\b", low))
        if score >= 2:
            return "hi"
        if score >= 1 and any(w in low for w in ("hai", "kya", "bolo", "mujhe")):
            return "hi"
        return "en"
