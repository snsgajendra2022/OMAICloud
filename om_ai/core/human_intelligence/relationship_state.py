"""Relationship state for human-context layer."""
from __future__ import annotations

from typing import Any


class RelationshipState:
    def __init__(self) -> None:
        self.familiarity = 0.4
        self.trust = 0.5
        self.address = "Sir"
        self.depth = "companion"

    def observe(self, *, emotion: str = "neutral", turns: int = 0) -> dict[str, Any]:
        if emotion in {"happy", "excitement"}:
            self.familiarity = min(1.0, self.familiarity + 0.02)
            self.trust = min(1.0, self.trust + 0.01)
        elif emotion in {"frustration", "stress", "sad"}:
            self.trust = min(1.0, self.trust + 0.015)  # showing up under stress builds trust
        if turns > 20:
            self.depth = "close_friend"
        elif turns > 5:
            self.depth = "friend"
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "familiarity": round(self.familiarity, 3),
            "trust": round(self.trust, 3),
            "address": self.address,
            "depth": self.depth,
        }
