"""Interruption manager for presence — stop speech immediately."""
from __future__ import annotations

import re
from typing import Any, Callable


class InterruptionManager:
    _STOP = re.compile(
        r"(?i)^\s*(stop|cancel|ruk|band karo|chup|bas|quiet|enough|wait)(?:\s|$)"
    )

    def __init__(self) -> None:
        self._stop_speech: Callable[[], None] | None = None

    def bind_stop(self, fn: Callable[[], None] | None) -> None:
        self._stop_speech = fn

    def assess(self, text: str) -> dict[str, Any]:
        t = (text or "").strip()
        if self._STOP.search(t):
            return {"interrupt": True, "kind": "stop", "should_stop_speech": True}
        return {"interrupt": False, "kind": "none", "should_stop_speech": False}

    def fire(self) -> dict[str, Any]:
        if self._stop_speech:
            try:
                self._stop_speech()
            except Exception:
                pass
        return {"stopped": True, "phase": "interrupted"}
