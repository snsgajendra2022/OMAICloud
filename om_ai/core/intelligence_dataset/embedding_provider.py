"""
OM Intelligence Embedding Provider.

The dataset system should not depend directly on one embedding
implementation.

Architecture:

    SemanticRetriever
          |
          v
    EmbeddingProvider
          |
    +-----+----------------+
    |                      |
Local Model           Future Provider
    |                      |
sentence-transformers     API
Ollama                    etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from typing import Sequence
import re


Vector = list[float]


class EmbeddingProvider(ABC):
    """
    Abstract embedding provider.

    Implementations must convert text into a numeric vector.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed(self, text: str) -> Vector:
        raise NotImplementedError

    def embed_many(
        self,
        texts: Sequence[str],
    ) -> list[Vector]:

        return [
            self.embed(text)
            for text in texts
        ]


class HashEmbeddingProvider(
    EmbeddingProvider
):
    """
    Deterministic development fallback.

    IMPORTANT:
    This is NOT a replacement for a neural embedding model.

    It exists so the retrieval architecture can run even when
    an embedding dependency/model is not installed.

    Production semantic quality should use a real embedding model.
    """

    def __init__(
        self,
        dimension: int = 384,
    ) -> None:

        if dimension < 32:

            raise ValueError(
                "Embedding dimension must be >= 32."
            )

        self._dimension = dimension

    @property
    def dimension(self) -> int:

        return self._dimension

    def embed(
        self,
        text: str,
    ) -> Vector:

        vector = [
            0.0
            for _ in range(self._dimension)
        ]

        tokens = re.findall(
            r"\w+",
            (text or "").lower(),
        )

        if not tokens:

            return vector

        for token in tokens:

            # Stable hash independent of Python's
            # randomized hash seed.
            value = 2166136261

            for char in token:

                value ^= ord(char)

                value = (
                    value * 16777619
                ) & 0xFFFFFFFF

            index = (
                value
                % self._dimension
            )

            sign = (
                1.0
                if value & 1
                else -1.0
            )

            vector[index] += sign

        return self._normalize(
            vector
        )

    @staticmethod
    def _normalize(
        vector: Vector,
    ) -> Vector:

        norm = sqrt(
            sum(
                value * value
                for value in vector
            )
        )

        if norm == 0.0:

            return vector

        return [
            value / norm
            for value in vector
        ]


class SentenceTransformerEmbeddingProvider(
    EmbeddingProvider
):
    """
    Optional neural embedding provider.

    Requires:

        pip install sentence-transformers

    Example model:

        sentence-transformers/all-MiniLM-L6-v2

    The model is loaded lazily.
    """

    def __init__(
        self,
        model_name: str = (
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
    ) -> None:

        self.model_name = model_name

        self._model = None

    def _load(self):

        if self._model is not None:

            return self._model

        try:

            from sentence_transformers import (
                SentenceTransformer,
            )

        except ImportError as exc:

            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Install it with: "
                "pip install sentence-transformers"
            ) from exc

        self._model = SentenceTransformer(
            self.model_name
        )

        return self._model

    @property
    def dimension(self) -> int:

        model = self._load()

        dimension = (
            model.get_sentence_embedding_dimension()
        )

        if dimension is None:

            raise RuntimeError(
                "Embedding model did not expose its dimension."
            )

        return int(dimension)

    def embed(
        self,
        text: str,
    ) -> Vector:

        model = self._load()

        vector = model.encode(
            text or "",
            normalize_embeddings=True,
        )

        return [
            float(value)
            for value in vector
        ]

    def embed_many(
        self,
        texts: Sequence[str],
    ) -> list[Vector]:

        model = self._load()

        vectors = model.encode(
            list(texts),
            normalize_embeddings=True,
        )

        return [
            [
                float(value)
                for value in vector
            ]
            for vector in vectors
        ]


def cosine_similarity(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    """
    Calculate cosine similarity.

    Expected range:

        -1.0 ... 1.0
    """

    if len(left) != len(right):

        raise ValueError(
            "Vectors must have the same dimension."
        )

    left_norm = sqrt(
        sum(
            value * value
            for value in left
        )
    )

    right_norm = sqrt(
        sum(
            value * value
            for value in right
        )
    )

    if (
        left_norm == 0.0
        or right_norm == 0.0
    ):

        return 0.0

    return (
        sum(
            a * b
            for a, b in zip(
                left,
                right,
            )
        )
        / (left_norm * right_norm)
    )