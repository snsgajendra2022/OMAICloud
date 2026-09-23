"""Embedding engine adapter for knowledge intelligence."""
from __future__ import annotations

from typing import Any


class EmbeddingEngine:
    def embed(self, texts: list[str]) -> list[Any]:
        try:
            from om_ai.core.knowledge.embedding_engine import EmbeddingEngine as EE

            return EE().embed(texts)
        except Exception:
            return [[0.0] for _ in texts]
