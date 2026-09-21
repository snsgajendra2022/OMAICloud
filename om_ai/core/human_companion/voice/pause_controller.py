"""Pause controller — insert natural pauses for companion speech."""
from __future__ import annotations

import re


class PauseController:
    def apply(self, text: str, *, emotion: str = "calm") -> str:
        t = (text or "").strip()
        if not t:
            return t
        # After Sir / Ji only when followed by comma/space — never shatter existing "..."
        t = re.sub(r"(?i)\b(sir|ji)\b\s*,\s*", r"\1... ", t, count=1)
        t = re.sub(r"(?i),\s*let me\b", "... let me", t)
        if emotion in {"soft", "stress", "sad", "frustration"} and "..." not in t:
            t = re.sub(r"\.\s+", "... ", t, count=1)
        t = re.sub(r"\.{4,}", "...", t)
        t = re.sub(r"\.\s+\.\s+\.", "...", t)
        return t.strip()
