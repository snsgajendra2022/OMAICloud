"""Interruption handler — barge-in / stop / redirect."""
from __future__ import annotations

import re
from typing import Any


class InterruptionHandler:
    _STOP = re.compile(
        r"(?i)^\s*(stop|cancel|ruk|band karo|chup|bas|quiet|enough)(?:\s|$)"
    )
    _REDIRECT = re.compile(r"(?i)\b(actually|wait|no\s+wait|instead|baat\s+sun)\b")

    def assess(self, message: str) -> dict[str, Any]:
        text = (message or "").strip()
        if self._STOP.search(text):
            return {"interrupted": True, "kind": "stop", "should_stop_speech": True}
        if self._REDIRECT.search(text):
            return {"interrupted": True, "kind": "redirect", "should_stop_speech": True}
        return {"interrupted": False, "kind": "none", "should_stop_speech": False}
