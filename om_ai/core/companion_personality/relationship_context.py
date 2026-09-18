"""Relationship depth from session history (structural, not keyword lists)."""
from __future__ import annotations

from typing import Any


class RelationshipContext:
    def assess(
        self,
        *,
        history: list[dict[str, Any]] | None,
        turn_count: int = 0,
    ) -> dict[str, Any]:
        hist = history or []
        user_turns = sum(1 for h in hist if h.get("role") == "user")
        total = turn_count or len(hist)
        depth = "new"
        if user_turns >= 8 or total >= 16:
            depth = "established"
        elif user_turns >= 3 or total >= 6:
            depth = "warming"
        familiarity = min(1.0, user_turns / 12.0)
        return {
            "depth": depth,
            "user_turns": user_turns,
            "total_turns": total,
            "familiarity": round(familiarity, 3),
        }
