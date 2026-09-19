"""Speech timing — natural sentence pacing (no robotic rush)."""
from __future__ import annotations

import re
from typing import Any


class SpeechTiming:
    def apply(self, text: str, *, emotion: str = "calm") -> dict[str, Any]:
        t = (text or "").strip()
        # Ensure sentence boundaries have breathing room markers for TTS humanize
        t = re.sub(r"\s*([.!?।])\s*", r"\1 ", t)
        t = re.sub(r"\s+", " ", t).strip()
        # Light ellipsis after greetings / acknowledgements
        t = re.sub(r"(?i)^(hello sir|hi sir|ji sir|theek hai|okay|haan)([,. ]+)", r"\1... ", t)
        return {"spoken": t, "emotion": emotion}
