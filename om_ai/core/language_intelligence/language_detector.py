from __future__ import annotations
import re

_DEV = re.compile(r"[\u0900-\u097F]")
_HING = re.compile(
    r"(?i)\b(hai|hain|ho|kya|kyu|kyun|nahi|mat|theek|bhai|yaar|bolo|batao|"
    r"kal|aaj|mujhe|tum|aap|karna|karo|project|complete)\b"
)

class LanguageDetector:
    def detect(self, text: str) -> dict:
        raw = text or ""
        has_dev = bool(_DEV.search(raw))
        has_lat = bool(re.search(r"[A-Za-z]", raw))
        hinglish = bool(_HING.search(raw)) and has_lat
        if has_dev and has_lat:
            mix = "hi-en"
        elif has_dev:
            mix = "hi"
        elif hinglish:
            mix = "hi-en"
        else:
            mix = "en"
        return {"locale": "hi" if mix.startswith("hi") else "en", "mix": mix, "devanagari": has_dev}
