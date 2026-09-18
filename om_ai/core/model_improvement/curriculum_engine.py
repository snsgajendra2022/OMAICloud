"""STEP 28 — Curriculum engine for native model improvement."""
from __future__ import annotations

from typing import Any


class CurriculumEngine:
    TRACKS = ("conversation", "coding", "reasoning", "knowledge", "safety")

    def build(self, gaps: list[str] | None = None) -> dict[str, Any]:
        gaps = list(gaps or [])
        lessons = []
        for track in self.TRACKS:
            weight = 1.2 if track in gaps or any(track in g for g in gaps) else 1.0
            lessons.append(
                {
                    "track": track,
                    "weight": weight,
                    "examples": 50 if weight > 1 else 20,
                    "focus": gaps or ["general_quality"],
                }
            )
        return {"lessons": lessons, "priority": sorted(lessons, key=lambda x: -x["weight"])}
