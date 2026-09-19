from __future__ import annotations
from typing import Any

class RealtimeState:
    def __init__(self) -> None:
        self.mode = "idle"
        self.listening = False
        self.speaking = False
        self.memory_line = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "listening": self.listening,
            "speaking": self.speaking,
            "memory": self.memory_line,
        }
