"""Relationship state — trust / familiarity over time."""
from __future__ import annotations

from typing import Any


class RelationshipState:
    def __init__(self) -> None:
        self.turns = 0
        self.familiarity = 0.2
        self.trust = 0.5

    def observe(self, *, emotion: str = "neutral") -> dict[str, Any]:
        self.turns += 1
        self.familiarity = min(1.0, 0.2 + self.turns * 0.03)
        if emotion in {"happy", "excitement"}:
            self.trust = min(1.0, self.trust + 0.02)
        elif emotion in {"frustration", "stress"}:
            self.trust = max(0.2, self.trust - 0.01)
        level = "new"
        if self.familiarity > 0.7:
            level = "close"
        elif self.familiarity > 0.4:
            level = "familiar"
        return {
            "turns": self.turns,
            "familiarity": round(self.familiarity, 3),
            "trust": round(self.trust, 3),
            "level": level,
            "address": "Sir" if self.familiarity > 0.35 else "",
        }
