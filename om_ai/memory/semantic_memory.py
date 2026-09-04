"""
OM Semantic Memory — personal knowledge / facts / preferences.
"""
from __future__ import annotations

from typing import Any

from om_ai.memory.storage import MemoryStorage
from om_ai.memory.models import MemoryItem


class SemanticMemory:
    """Long-lived personal knowledge nodes (facts, prefs, concepts)."""

    def __init__(self, storage: MemoryStorage | None = None) -> None:
        self.storage = storage or MemoryStorage()

    def remember(
        self,
        content: str,
        *,
        kind: str = "fact",
        importance: float = 0.8,
        project: str | None = None,
        tags: list[str] | None = None,
    ) -> int:
        return int(
            self.storage.save(
                MemoryItem(
                    id=None,
                    content=(content or "").strip(),
                    memory_type="semantic" if kind == "fact" else kind,
                    project=project,
                    tags=tags or ["semantic", kind],
                    importance=float(importance),
                )
            )
        )

    def remember_preference(self, content: str) -> int:
        return self.remember(content, kind="preference", importance=0.85, tags=["preference"])

    def recall(self, query: str, *, k: int = 8) -> list[dict[str, Any]]:
        q = (query or "").strip().lower()
        rows = self.storage.all() or []
        hits: list[dict[str, Any]] = []
        for row in rows:
            if len(row) < 3:
                continue
            mem_type = str(row[2] or "")
            if mem_type not in {"semantic", "fact", "preference", "long_term", "personal"}:
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
            if score > 0 or not q:
                hits.append(
                    {
                        "id": row[0],
                        "content": content,
                        "type": mem_type,
                        "score": score or 0.1,
                        "importance": float(row[5] or 0.5) if len(row) > 5 else 0.5,
                    }
                )
        hits.sort(key=lambda x: (x["score"], x["importance"]), reverse=True)
        return hits[:k]
