"""Retrieval service — dedicated vector search facade."""
from __future__ import annotations

from typing import Any

from services._common import ServiceHealth, ok


class RetrievalService:
    def health(self) -> dict[str, Any]:
        return ServiceHealth("retrieval-service", detail={"backend": "PersistentKnowledgeBase TF-IDF"}).to_dict()

    def search(self, query: str, *, k: int = 5, tenant_id: str = "default") -> dict[str, Any]:
        from om_ai.knowledge.retrieval import VectorKnowledgeLayer

        hits = VectorKnowledgeLayer(tenant_id=tenant_id).search(query, k=k)
        # confidence proxy = normalized score if present
        for h in hits:
            score = float(h.get("score") or 0.0)
            h["confidence"] = round(min(1.0, max(0.0, score)), 4)
        return ok({"query": query, "hits": hits, "k": k})
