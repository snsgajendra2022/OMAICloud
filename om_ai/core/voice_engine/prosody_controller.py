"""Natural pauses / whisper / speed shaping for TTS."""
from __future__ import annotations

import re


class ProsodyController:
    def apply(self, text: str, *, presence: str = "speaking") -> str:
        t = (text or "").strip()
        if not t or "[[slnc" in t.lower():
            return t
        # Presence-aware pause lengths
        comma = 200
        stop = 420
        if presence in {"thinking", "remembering", "concerned"}:
            comma, stop = 280, 560
        elif presence == "excited":
            comma, stop = 140, 300
        elif presence == "explaining":
            comma, stop = 220, 480
        t = re.sub(r"\s*—\s*", f" [[slnc {comma + 40}]] ", t)
        t = re.sub(r"([,;:])\s+", rf"\1 [[slnc {comma}]] ", t)
        t = re.sub(r"([.!?])\s+", rf"\1 [[slnc {stop}]] ", t)
        t = re.sub(r"(।)\s*", rf"\1 [[slnc {stop - 40}]] ", t)
        # Jarvis breath after Sir
        t = re.sub(r"(?i)\b(sir)\b([,.!]?)(\s+)", rf"\1\2 [[slnc {comma}]] \3", t)
        return t.strip()
