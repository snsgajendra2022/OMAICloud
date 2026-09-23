"""Knowledge Intelligence façade — vector retrieval, NOT 100M prompts in context.

Real implementation lives in om_ai.knowledge + knowledge_intelligence.
"""
from __future__ import annotations

from typing import Any

__all__ = [
    "document_loader",
    "embedding_engine",
    "vector_database",
    "knowledge_graph",
    "retrieval_engine",
    "retrieve",
]


def retrieve(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    from .retrieval_engine import RetrievalEngine

    return RetrievalEngine().search(query, limit=limit)
