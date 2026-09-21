"""Track partial / accumulating transcripts across a listen window."""
from __future__ import annotations

import time
from typing import Any


class PartialTranscript:
    def __init__(self) -> None:
        self.text = ""
        self.updates = 0
        self._started_ms = 0.0
        self._last_ms = 0.0

    def update(self, text: str) -> dict[str, Any]:
        t = (text or "").strip()
        now = time.time() * 1000
        if not self._started_ms:
            self._started_ms = now
        # Prefer longer / newer partials (browser often revises)
        if len(t) >= len(self.text) or not self.text:
            self.text = t
        self.updates += 1
        self._last_ms = now
        return {
            "partial": self.text,
            "updates": self.updates,
            "age_ms": now - self._started_ms,
            "idle_ms": 0.0,
        }

    def idle_ms(self) -> float:
        if not self._last_ms:
            return 0.0
        return time.time() * 1000 - self._last_ms

    def clear(self) -> None:
        self.text = ""
        self.updates = 0
        self._started_ms = 0.0
        self._last_ms = 0.0
