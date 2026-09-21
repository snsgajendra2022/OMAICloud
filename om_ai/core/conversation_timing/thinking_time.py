"""Thinking-time budget before committing a reply."""
from __future__ import annotations

from typing import Any


class ThinkingTime:
    def budget(self, *, complexity: str = "normal", emotion: str = "neutral") -> dict[str, Any]:
        base = {"light": 180, "normal": 320, "heavy": 650}.get(complexity, 320)
        if emotion in {"sad", "stressed", "frustrated"}:
            base += 160
        return {"think_ms": base, "stream_early": complexity != "heavy"}
