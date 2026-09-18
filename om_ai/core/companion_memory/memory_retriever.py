"""Retrieve memory slices for a query."""
from __future__ import annotations

from typing import Any

from .memory_ranker import MemoryRanker


class MemoryRetriever:
    def __init__(self, ranker: MemoryRanker | None = None) -> None:
        self.ranker = ranker or MemoryRanker()

    def gather_pool(
        self,
        *,
        episodic: list[dict[str, Any]],
        semantic: list[dict[str, Any]],
        preferences: list[dict[str, Any]],
        project: list[dict[str, Any]],
        working: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        pool: list[dict[str, Any]] = []
        pool.extend(working)
        pool.extend(preferences)
        pool.extend(semantic)
        pool.extend(project)
        pool.extend(episodic)
        return pool

    def retrieve(
        self,
        query: str,
        *,
        episodic: list[dict[str, Any]],
        semantic: list[dict[str, Any]],
        preferences: list[dict[str, Any]],
        project: list[dict[str, Any]],
        working: list[dict[str, Any]],
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        pool = self.gather_pool(
            episodic=episodic,
            semantic=semantic,
            preferences=preferences,
            project=project,
            working=working,
        )
        return self.ranker.rank(pool, query, limit=limit)

    def context_blob(self, hits: list[dict[str, Any]], *, max_chars: int = 1200) -> str:
        parts: list[str] = []
        for h in hits:
            kind = h.get("kind") or "mem"
            preview = str(h.get("content") or "")[:200]
            parts.append(f"[{kind}] {preview}")
        blob = "\n".join(parts)
        return blob[:max_chars]
