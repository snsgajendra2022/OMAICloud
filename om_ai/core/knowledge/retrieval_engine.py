"""Retrieval engine — docs → embeddings → vector search → relevant chunks."""
from __future__ import annotations

from typing import Any

from .vector_database import VectorDatabase


class RetrievalEngine:
    def __init__(self) -> None:
        self.db = VectorDatabase()

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        return self.db.search(query, limit=limit)


retrieval_engine = RetrievalEngine
