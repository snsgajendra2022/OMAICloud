"""Speech timing — natural sentence pacing (no robotic rush)."""
from __future__ import annotations

import re
from typing import Any


class SpeechTiming:
    def apply(self, text: str, *, emotion: str = "calm") -> dict[str, Any]:
        t = (text or "").strip()
        # Protect ellipsis before normalizing sentence punctuation
        t = t.replace("…", "...")
        t = re.sub(r"\.{3,}", "«ELLIP»", t)
        t = re.sub(r"\s*([.!?।])\s*", r"\1 ", t)
        t = t.replace("«ELLIP»", "...")
        t = re.sub(r"\s+", " ", t).strip()
        # Light ellipsis after greetings / acknowledgements (only if missing)
        if not re.search(r"(?i)^(hello sir|hi sir|ji sir|theek hai|okay|haan)\.\.\.", t):
            t = re.sub(
                r"(?i)^(hello sir|hi sir|ji sir|theek hai|okay|haan)([,. ]+)",
                r"\1... ",
                t,
            )
        return {"spoken": t, "emotion": emotion}
