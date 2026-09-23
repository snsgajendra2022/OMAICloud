"""Vector memory — retrieval store façade (not millions of prompts)."""
from __future__ import annotations

from typing import Any


class VectorMemory:
    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        try:
            from om_ai.core.knowledge.vector_database import VectorDatabase

            return VectorDatabase().search(query, limit=limit)
        except Exception:
            return []
