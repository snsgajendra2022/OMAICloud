"""Human-like response timing / pause hints."""
from __future__ import annotations

from typing import Any


class ResponseTiming:
    def plan(self, *, presence_mode: str = "attentive", text_len: int = 0) -> dict[str, Any]:
        think_ms = 280
        if presence_mode in {"thinking", "remembering"}:
            think_ms = 650
        elif presence_mode in {"concerned", "confused"}:
            think_ms = 480
        elif presence_mode == "excited":
            think_ms = 180
        speak_gap_ms = 120 if text_len < 80 else 220
        return {
            "pre_think_ms": think_ms,
            "speak_gap_ms": speak_gap_ms,
            "allow_barge_in": True,
            "natural_pause": True,
        }
