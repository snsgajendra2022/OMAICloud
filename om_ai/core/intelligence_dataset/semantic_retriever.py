"""
OM Semantic Dataset Retriever.

Pipeline:

    Query
      |
      v
    Embedding
      |
      v
    Vector Similarity
      |
      v
    Metadata Filtering
      |
      v
    Quality Filtering
      |
      v
    Ranked Results
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .dataset_item import DatasetItem
from .repository import DatasetRepository
from .embedding_provider import (
    EmbeddingProvider,
    HashEmbeddingProvider,
    cosine_similarity,
)
from .semantic_index import SemanticIndex
from .retrieval_result import RetrievalResult


class SemanticRetriever:

    def __init__(
        self,
        repository: DatasetRepository | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        semantic_index: SemanticIndex | None = None,
    ) -> None:

        self.repository = (
            repository
            or DatasetRepository()
        )

        self.embedding_provider = (
            embedding_provider
            or HashEmbeddingProvider()
        )

        self.semantic_index = (
            semantic_index
            or SemanticIndex()
        )

        self.model_name = (
            getattr(
                self.embedding_provider,
                "model_name",
                None,
            )
            or self.embedding_provider.__class__.__name__
        )

    # =========================================================
    # INDEX ONE ITEM
    # =========================================================

    def index_item(
        self,
        item: DatasetItem,
    ) -> None:

        # Build a richer semantic representation than only
        # input_text.

        searchable_text = (
            f"Input: {item.input_text}\n"
            f"Meaning: {item.meaning}\n"
            f"Intent: {item.intent}\n"
            f"Goal: {item.goal}\n"
            f"Domain: {item.domain}\n"
            f"Type: {item.dataset_type.value}\n"
            f"Tags: {' '.join(item.tags)}"
        )

        embedding = (
            self.embedding_provider.embed(
                searchable_text
            )
        )

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        self.semantic_index.save(
            item_id=item.item_id,
            embedding=embedding,
            model_name=self.model_name,
            timestamp=timestamp,
        )

    # =========================================================
    # INDEX MANY
    # =========================================================

    def index_items(
        self,
        items: list[DatasetItem],
    ) -> int:

        count = 0

        for item in items:

            self.index_item(item)

            count += 1

        return count

    # =========================================================
    # SEARCH
    # =========================================================

    def search(
        self,
        query: str,
        *,
        intent: str | None = None,
        domain: str | None = None,
        language: str | None = None,
        dataset_type: str | None = None,
        min_quality: float = 0.0,
        min_similarity: float = 0.30,
        limit: int = 5,
    ) -> list[RetrievalResult]:

        query = (
            query or ""
        ).strip()

        if not query:

            return []

        query_embedding = (
            self.embedding_provider.embed(
                query
            )
        )

        candidates = (
            self.semantic_index.all()
        )

        scored: list[
            tuple[DatasetItem, float]
        ] = []

        for (
            item_id,
            embedding,
            model_name,
        ) in candidates:

            item = self.repository.get(
                item_id
            )

            if item is None:
                continue

            # -------------------------------------------------
            # Metadata filters
            # -------------------------------------------------

            if intent and item.intent != intent:
                continue

            if domain and item.domain != domain:
                continue

            if language and item.language != language:
                continue

            if (
                dataset_type
                and item.dataset_type.value
                != dataset_type
            ):
                continue

            if (
                item.quality_score
                < min_quality
            ):
                continue

            # -------------------------------------------------
            # Similarity
            # -------------------------------------------------

            similarity = cosine_similarity(
                query_embedding,
                embedding,
            )

            if similarity < min_similarity:
                continue

            scored.append(
                (
                    item,
                    similarity,
                )
            )

        # Highest semantic similarity first.

        scored.sort(
            key=lambda pair: (
                pair[1],
                pair[0].quality_score,
            ),
            reverse=True,
        )

        results: list[
            RetrievalResult
        ] = []

        for rank, (
            item,
            similarity,
        ) in enumerate(
            scored[:max(1, limit)],
            start=1,
        ):

            results.append(
                RetrievalResult(

                    item=item,

                    similarity=similarity,

                    rank=rank,

                    retrieval_reason=(
                        "semantic_similarity"
                    ),

                    metadata={
                        "embedding_model":
                            self.model_name,

                        "quality_score":
                            item.quality_score,

                        "domain":
                            item.domain,

                        "intent":
                            item.intent,
                    },
                )
            )

        return results

    # =========================================================
    # ENSURE INDEX
    # =========================================================

    def ensure_indexed(
        self,
        item: DatasetItem,
    ) -> None:

        existing = (
            self.semantic_index.get(
                item.item_id
            )
        )

        if existing is None:

            self.index_item(item)

    # =========================================================
    # DELETE INDEX
    # =========================================================

    def delete(
        self,
        item_id: str,
    ) -> bool:

        return self.semantic_index.delete(
            item_id
        )

    # =========================================================
    # STATS
    # =========================================================

    def count_indexed(self) -> int:

        return self.semantic_index.count()