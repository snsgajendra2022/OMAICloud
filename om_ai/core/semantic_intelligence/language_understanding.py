"""Language understanding — normalize speech/text before intent."""
from __future__ import annotations

import re
from typing import Any


class LanguageUnderstanding:
    """Clean ASR noise, detect locale, extract simple entities."""

    _FILLERS = re.compile(
        r"(?i)\b(um+|uh+|ahh*|like|you know|basically|actually|matlab|yaani)\b"
    )
    _DUP_WORDS = re.compile(r"\b(\w+)(\s+\1\b)+", re.I)
    _ASR_FIXES: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"(?i)^are\s+what\s+are\b"), "what are"),
        (re.compile(r"(?i)^what\s+what\b"), "what"),
        (re.compile(r"(?i)\bgoogle\s+search\s+karo\b"), "search"),
        (re.compile(r"(?i)\bkya\s+kar\s+rahe\s+ho\b"), "what are you doing"),
        (re.compile(r"(?i)\bkya\s+haal\s+hai\b"), "how are you"),
    ]

    def understand(self, text: str) -> dict[str, Any]:
        raw = (text or "").strip()
        cleaned = self._normalize(raw)
        locale = self._locale(cleaned)
        entities = self._entities(cleaned)
        speech_act = self._speech_act(cleaned)
        return {
            "raw": raw,
            "corrected": cleaned,
            "locale": locale,
            "entities": entities,
            "speech_act": speech_act,
            "is_hinglish": locale == "hi",
            "token_count": len(cleaned.split()),
        }

    def _normalize(self, text: str) -> str:
        t = re.sub(r"\s+", " ", (text or "").strip())
        t = self._FILLERS.sub(" ", t)
        t = self._DUP_WORDS.sub(r"\1", t)
        t = re.sub(r"\s+", " ", t).strip(" .,!?")
        for pat, repl in self._ASR_FIXES:
            t = pat.sub(repl, t)
        # "are what are you doing" → "what are you doing"
        t = re.sub(r"(?i)^(are|is|was)\s+(what|who|where|when|why|how)\b", r"\2", t)
        return t.strip() or (text or "").strip()

    def _locale(self, text: str) -> str:
        if re.search(
            r"[\u0900-\u097F]|\b(hai|hain|kya|tum|nahi|karo|batao|mujhe|bhai|theek)\b",
            (text or "").lower(),
        ):
            return "hi"
        return "en"

    def _entities(self, text: str) -> list[str]:
        ents: list[str] = []
        for m in re.finditer(
            r"(?i)\b(python|javascript|react|vscode|chrome|google|youtube|"
            r"project|server|bug|error|ai|om)\b",
            text or "",
        ):
            ents.append(m.group(1).lower())
        # URLs / paths lightly
        for m in re.finditer(r"https?://\S+|/[A-Za-z0-9_\-./]+", text or ""):
            ents.append(m.group(0)[:80])
        return list(dict.fromkeys(ents))[:12]

    def _speech_act(self, text: str) -> str:
        low = (text or "").lower()
        if "?" in (text or "") or re.search(
            r"(?i)^(what|who|where|when|why|how|kya|kaise|kyun)\b", low
        ):
            return "question"
        if re.search(r"(?i)\b(please|open|kholo|search|find|delete|send|run|do)\b", low):
            return "request"
        if re.search(r"(?i)\b(i feel|i am|i'm|today was|failed|tired|sad|happy)\b", low):
            return "share"
        if re.search(r"(?i)^(stop|cancel|quit|mute|bas)\b", low):
            return "command"
        return "statement"
