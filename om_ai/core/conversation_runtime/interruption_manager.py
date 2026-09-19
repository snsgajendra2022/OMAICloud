"""Handle barge-in and mid-speech redirects."""
from __future__ import annotations

import re
from typing import Any


class InterruptionManager:
    REDIRECT = re.compile(
        r"(?i)\b(no[, ]+|wait|stop|actually|instead|first|pehle|रुको|नहीं)\b"
    )

    def analyze(self, text: str, *, speaking: bool = False) -> dict[str, Any]:
        low = (text or "").strip()
        redirected = bool(self.REDIRECT.search(low))
        barge = speaking and (redirected or len(low.split()) >= 2)
        return {
            "barge_in": barge,
            "redirect": redirected,
            "should_stop_speech": barge,
            "priority": "high" if barge else "normal",
            "ack": (
                "Understood. I will switch focus."
                if redirected
                else ("I'm listening." if barge else "")
            ),
        }
