"""Natural pause / hold window for incomplete speech."""
from __future__ import annotations

import time
from typing import Any


class ConversationPause:
    def __init__(self, hold_ms: float = 900) -> None:
        self.hold_ms = hold_ms
        self._hold_until = 0.0
        self._buffer = ""

    def begin_hold(self, text: str, *, hold_ms: float | None = None) -> dict[str, Any]:
        self._buffer = (text or "").strip()
        ms = float(hold_ms if hold_ms is not None else self.hold_ms)
        self._hold_until = time.time() * 1000 + ms
        return {"holding": True, "buffer": self._buffer, "hold_ms": ms}

    def extend(self, text: str) -> dict[str, Any]:
        t = (text or "").strip()
        if t:
            # Merge continuation
            if self._buffer and t.lower().startswith(self._buffer.lower()[:12]):
                self._buffer = t
            elif self._buffer and not t.lower().startswith(self._buffer.lower()):
                self._buffer = f"{self._buffer} {t}".strip()
            else:
                self._buffer = t or self._buffer
        self._hold_until = time.time() * 1000 + self.hold_ms
        return {"holding": True, "buffer": self._buffer}

    def ready(self) -> dict[str, Any]:
        now = time.time() * 1000
        if not self._buffer:
            return {"ready": False, "reason": "empty"}
        if now < self._hold_until:
            return {
                "ready": False,
                "reason": "holding",
                "remaining_ms": self._hold_until - now,
                "buffer": self._buffer,
            }
        buf = self._buffer
        self._buffer = ""
        self._hold_until = 0.0
        return {"ready": True, "buffer": buf, "reason": "pause_elapsed"}

    def clear(self) -> None:
        self._buffer = ""
        self._hold_until = 0.0
