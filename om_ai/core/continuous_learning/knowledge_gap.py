"""STEP 29 — Knowledge gap registry."""
from __future__ import annotations

from collections import Counter
from typing import Any


class KnowledgeGapRegistry:
    def __init__(self) -> None:
        self._gaps: Counter[str] = Counter()
        self._examples: dict[str, list[str]] = {}

    def record(self, gap: str, example: str = "") -> None:
        g = (gap or "general").strip() or "general"
        self._gaps[g] += 1
        if example:
            self._examples.setdefault(g, []).append(example[:300])
            self._examples[g] = self._examples[g][-20:]

    def top(self, n: int = 10) -> list[dict[str, Any]]:
        return [
            {"gap": k, "count": v, "examples": list(self._examples.get(k) or [])[:3]}
            for k, v in self._gaps.most_common(n)
        ]

    def snapshot(self) -> dict[str, Any]:
        return {"gaps": self.top(), "total": int(sum(self._gaps.values()))}
