"""Streaming / partial transcript context."""
from __future__ import annotations

from typing import Any


class StreamingContext:
    def __init__(self) -> None:
        self.partial = ""
        self.final = ""
        self.partial_count = 0

    def on_partial(self, text: str) -> dict[str, Any]:
        self.partial = (text or "").strip()
        self.partial_count += 1
        return {
            "partial": self.partial,
            "ready_enough": len(self.partial.split()) >= 4,
            "count": self.partial_count,
        }

    def on_final(self, text: str) -> dict[str, Any]:
        self.final = (text or "").strip()
        self.partial = ""
        return {"final": self.final, "partial_count": self.partial_count}
