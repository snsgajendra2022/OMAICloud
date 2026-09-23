"""Knowledge graph adapter."""
from __future__ import annotations

from typing import Any


class KnowledgeGraph:
    def related(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        try:
            from om_ai.core.knowledge_intelligence.knowledge_graph import KnowledgeGraph as KG

            kg = KG()
            if hasattr(kg, "query"):
                return list(kg.query(query) or [])[:limit]
            if hasattr(kg, "related"):
                return list(kg.related(query) or [])[:limit]
        except Exception:
            pass
        return []


knowledge_graph = KnowledgeGraph
