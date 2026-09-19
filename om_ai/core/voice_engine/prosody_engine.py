"""Prosody engine — light pauses, presence-aware timing (Aman-friendly)."""
from __future__ import annotations

import re
from typing import Any


class ProsodyEngine:
    def __init__(
        self,
        pause_short: int = 70,
        pause_medium: int = 120,
        pause_long: int = 160,
    ) -> None:
        self.pause_short = pause_short
        self.pause_medium = pause_medium
        self.pause_long = pause_long

    def apply(self, text: str, *, presence: str = "speaking") -> str:
        t = (text or "").strip()
        if not t or "[[slnc" in t.lower():
            return t

        comma = self.pause_short
        stop = self.pause_long
        if presence in {"thinking", "remembering", "concerned"}:
            comma, stop = 95, 175
        elif presence == "excited":
            comma, stop = 55, 110
        elif presence == "explaining":
            comma, stop = 75, 145

        t = re.sub(r"\s*—\s*", f" [[slnc {comma + 20}]] ", t)
        t = re.sub(r"([,;:])\s+", rf"\1 [[slnc {comma}]] ", t)
        t = re.sub(r"([.!?])\s+", rf"\1 [[slnc {stop}]] ", t)
        t = re.sub(r"(।)\s*", rf"\1 [[slnc {stop}]] ", t)
        t = re.sub(r"(?i)\b(sir|ji)\b([,.!]?)(\s+)", rf"\1\2 [[slnc {comma}]] \3", t)
        return t.strip()

    def apply_xml(self, text: str) -> str:
        """SSML-style breaks for neural providers."""
        if not text:
            return ""
        speech = text.strip()
        speech = re.sub(r",\s+", f", <break {self.pause_short}ms/> ", speech)
        speech = re.sub(r"\s[-—]\s", f" <break {self.pause_medium}ms/> ", speech)
        speech = re.sub(r"\.\s+", f". <break {self.pause_long}ms/> ", speech)
        speech = re.sub(r"\?\s+", f"? <break {self.pause_medium}ms/> ", speech)
        return speech

    def speaking_style(self, emotion: str = "neutral") -> dict[str, Any]:
        styles = {
            "neutral": {"speed": 1.0, "energy": 0.55},
            "happy": {"speed": 1.04, "energy": 0.72},
            "concerned": {"speed": 0.94, "energy": 0.42},
            "focused": {"speed": 0.98, "energy": 0.6},
            "calm": {"speed": 1.0, "energy": 0.5},
            "excited": {"speed": 1.06, "energy": 0.82},
            "soft": {"speed": 0.91, "energy": 0.35},
        }
        return styles.get(emotion, styles["neutral"])


# Back-compat alias
ProsodyController = ProsodyEngine
