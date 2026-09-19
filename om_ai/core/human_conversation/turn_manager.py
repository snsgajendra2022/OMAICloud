from __future__ import annotations
import time
from typing import Any

class TurnManager:
    def __init__(self) -> None:
        self.history: list[dict[str, Any]] = []

    def add(self, role: str, text: str, *, intent: str = "") -> None:
        self.history.append({
            "role": role,
            "text": text,
            "intent": intent,
            "ts": time.time(),
        })
        self.history = self.history[-60:]

    def recent(self, n: int = 8) -> list[dict[str, Any]]:
        return list(self.history[-n:])
