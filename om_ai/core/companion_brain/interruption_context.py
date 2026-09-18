"""Detect and track user interruptions / topic shifts."""
from __future__ import annotations

import re
from typing import Any


class InterruptionContext:
    _SHIFT = re.compile(
        r"^\s*(actually|wait|stop|never\s*mind|instead|rather|switch|new\s+topic)\b",
        re.I,
    )
    _BARGE = re.compile(r"^\s*(hold\s+on|one\s+sec|quick\s+question)\b", re.I)

    def analyze(
        self,
        message: str,
        *,
        session_interrupted: bool = False,
    ) -> dict[str, Any]:
        text = (message or "").strip()
        topic_shift = bool(self._SHIFT.search(text))
        barge_in = bool(self._BARGE.search(text))
        interrupted = session_interrupted or topic_shift or barge_in
        return {
            "topic_shift": topic_shift,
            "barge_in": barge_in,
            "interrupted": interrupted,
            "handling": "reset_thread" if topic_shift else ("yield" if barge_in else "normal"),
        }
