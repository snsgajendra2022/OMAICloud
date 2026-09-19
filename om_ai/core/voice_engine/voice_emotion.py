"""Emotion-conditioned phrasing for spoken delivery."""
from __future__ import annotations

import re


class VoiceEmotion:
    def apply(self, text: str, *, emotion: str = "calm") -> str:
        t = (text or "").strip()
        if not t:
            return t
        e = (emotion or "calm").lower()
        if e in {"concerned", "soft"} and not t.lower().startswith(("i ", "sir", "haan", "of course")):
            if not re.search(r"(?i)^(i understand|i hear|samajh|theek)", t):
                pass  # keep text; prosody handles softness
        if e == "excited" and t.endswith("."):
            t = t[:-1] + "."
        if e == "whisper":
            # macOS say supports [[volm 0.3]]
            t = f"[[volm 0.35]] {t}"
        return t
