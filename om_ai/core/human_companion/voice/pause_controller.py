"""Pause controller — insert natural pauses for companion speech."""
from __future__ import annotations

import re
from typing import Any


class PauseController:
    def apply(self, text: str, *, emotion: str = "calm") -> str:
        t = (text or "").strip()
        if not t:
            return t
        # After Sir / Ji acknowledgements
        t = re.sub(r"(?i)\b(sir|ji)\b\s*[, ]\s*", r"\1... ", t, count=1)
        # Soft pause before "let me"
        t = re.sub(r"(?i),\s*let me\b", "... let me", t)
        if emotion in {"soft", "stress", "sad", "frustration"}:
            t = re.sub(r"\.\s+", "... ", t, count=1)
        return re.sub(r"\.{4,}", "...", t).strip()
