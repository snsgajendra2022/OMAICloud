"""Embedding engine adapter → om_ai.knowledge.embeddings."""
from __future__ import annotations

from typing import Any


class EmbeddingEngine:
    def embed(self, texts: list[str]) -> list[Any]:
        try:
            from om_ai.knowledge import embeddings as emb

            if hasattr(emb, "embed"):
                return list(emb.embed(texts))
            if hasattr(emb, "EmbeddingEngine"):
                return list(emb.EmbeddingEngine().embed(texts))
        except Exception:
            pass
        return [[0.0] for _ in texts]


embedding_engine = EmbeddingEngine
