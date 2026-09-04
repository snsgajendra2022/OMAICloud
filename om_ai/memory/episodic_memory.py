"""
OM Episodic Memory — experience of past Q→A / task outcomes.
"""
from __future__ import annotations

from typing import Any

from om_ai.memory.storage import MemoryStorage
from om_ai.memory.models import MemoryItem


class EpisodicMemory:
    """Stores successful (and failed) reasoning episodes for reuse."""

    def __init__(self, storage: MemoryStorage | None = None) -> None:
        self.storage = storage or MemoryStorage()

    def remember(
        self,
        question: str,
        solution: str,
        *,
        score: float = 0.7,
        tags: list[str] | None = None,
    ) -> int:
        content = f"Q: {(question or '').strip()}\nA: {(solution or '').strip()}"
        return int(
            self.storage.save(
                MemoryItem(
                    id=None,
                    content=content,
                    memory_type="experience",
                    tags=tags or ["episodic"],
                    importance=float(score),
                )
            )
        )

    def recall(self, query: str, *, k: int = 5) -> list[dict[str, Any]]:
        q = (query or "").strip().lower()
        rows = self.storage.all() or []
        hits: list[dict[str, Any]] = []
        for row in rows:
            # row: id, content, memory_type, project, tags, importance, created_at
            if len(row) < 3:
                continue
            mem_type = str(row[2] or "")
            if mem_type not in {"experience", "episodic"}:
                continue
            content = str(row[1] or "")
            if not content:
                continue
            cl = content.lower()
            score = 0.0
            if q and q in cl:
                score += 3.0
            for tok in q.split():
                if len(tok) >= 2 and tok in cl:
                    score += 1.0
            if score <= 0 and not q:
                score = 0.1
            if score > 0:
                hits.append(
                    {
                        "id": row[0],
                        "content": content,
                        "type": "episodic",
                        "score": score,
                        "importance": float(row[5] or 0.5) if len(row) > 5 else 0.5,
                    }
                )
        hits.sort(key=lambda x: (x["score"], x["importance"]), reverse=True)
        return hits[:k]
