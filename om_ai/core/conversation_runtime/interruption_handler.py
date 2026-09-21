"""Realtime interruption — barge-in stops TTS immediately."""
from __future__ import annotations

import re
from typing import Any, Callable


class RealtimeInterruptionHandler:
    _STOP = re.compile(
        r"(?i)^\s*(stop|cancel|ruk|band karo|chup|bas|quiet|enough)(?:\s|$)"
    )
    _BARGE = re.compile(r"(?i)\b(wait|actually|no wait|sun|ruk)\b")

    def __init__(self) -> None:
        self._stop_fn: Callable[[], None] | None = None
        self.speaking = False

    def bind(self, stop_fn: Callable[[], None] | None) -> None:
        self._stop_fn = stop_fn

    def set_speaking(self, speaking: bool) -> None:
        self.speaking = speaking

    def handle(self, text: str) -> dict[str, Any]:
        t = (text or "").strip()
        if self._STOP.search(t) or (self.speaking and self._BARGE.search(t)):
            if self._stop_fn:
                try:
                    self._stop_fn()
                except Exception:
                    pass
            self.speaking = False
            return {
                "interrupted": True,
                "should_stop_speech": True,
                "continue_conversation": True,
            }
        return {"interrupted": False, "should_stop_speech": False, "continue_conversation": True}
