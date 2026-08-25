"""Knowledge microservice + factory."""
from __future__ import annotations

from typing import Any

from services._common import ServiceHealth, ok


class KnowledgeService:
    def health(self) -> dict[str, Any]:
        return ServiceHealth("knowledge-service").to_dict()

    def search(self, query: str, *, k: int = 5) -> dict[str, Any]:
        from om_ai.knowledge.retrieval import VectorKnowledgeLayer

        return ok(VectorKnowledgeLayer().search(query, k=k))

    def ingest(self, path: str) -> dict[str, Any]:
        from om_ai.knowledge.factory import process_document

        return ok(process_document(path))
