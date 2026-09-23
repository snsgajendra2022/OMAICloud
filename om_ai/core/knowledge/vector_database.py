"""Vector database adapter."""
from __future__ import annotations

from typing import Any


class VectorDatabase:
    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        try:
            from om_ai.knowledge.rag import retrieve  # type: ignore

            rows = retrieve(query, limit=limit) or []
            out = []
            for r in rows:
                out.append(
                    {
                        "text": str(getattr(r, "text", None) or r)[:500],
                        "score": float(getattr(r, "score", 0) or 0),
                    }
                )
            return out
        except Exception:
            return []


vector_database = VectorDatabase
