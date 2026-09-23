"""Emotional memory — recent affect trail."""
from __future__ import annotations

from typing import Any

from .emotional_context import EmotionalContext


class EmotionalMemory:
    def __init__(self) -> None:
        self.ctx = EmotionalContext()

    def remember(self, emotion: str) -> None:
        try:
            self.ctx.add({"emotion": emotion})
        except Exception:
            pass

    def recent(self) -> list[str]:
        try:
            return list(self.ctx.recent_labels() if hasattr(self.ctx, "recent_labels") else [])
        except Exception:
            return []
