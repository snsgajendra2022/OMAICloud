"""
OM Intelligence Dataset configuration.
"""

from __future__ import annotations

from .embedding_provider import (
    EmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)


EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


def create_embedding_provider() -> EmbeddingProvider:
    return SentenceTransformerEmbeddingProvider(
        EMBEDDING_MODEL
    )