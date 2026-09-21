"""Adaptive pre-response delay (never fake filler speech)."""
from __future__ import annotations

from typing import Any


class ResponseDelay:
    def plan(
        self,
        *,
        emotion: str = "neutral",
        complete: bool = True,
        conversation_need: str = "steady",
        word_count: int = 0,
    ) -> dict[str, Any]:
        # No spoken "thinking…" — silence timing only
        ms = 220
        if conversation_need in {"listen_first", "support_and_listen"}:
            ms = 520
        elif emotion in {"sad", "stressed", "frustrated", "tired"}:
            ms = 450
        elif emotion in {"happy", "excited", "urgent"}:
            ms = 140
        if not complete:
            ms = max(ms, 700)
        if word_count >= 18:
            ms += 120
        return {
            "delay_ms": ms,
            "speak_filler": False,
            "allow_barge_in": True,
        }
