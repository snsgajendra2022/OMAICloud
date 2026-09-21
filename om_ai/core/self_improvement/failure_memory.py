"""Remember failures for offline improvement (not live training)."""
from __future__ import annotations

import time
from typing import Any


class FailureMemory:
    def __init__(self) -> None:
        self.failures: list[dict[str, Any]] = []

    def remember(self, *, kind: str, detail: str, user_message: str = "") -> dict[str, Any]:
        item = {
            "ts": time.time(),
            "kind": kind,
            "detail": detail[:400],
            "user_message": (user_message or "")[:200],
        }
        self.failures.append(item)
        self.failures = self.failures[-200:]
        return item

    def recent(self, n: int = 20) -> list[dict[str, Any]]:
        return list(self.failures[-n:])
