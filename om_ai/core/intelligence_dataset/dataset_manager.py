"""
OM Intelligence Dataset Manager.

Production application service responsible for:

- Dataset validation
- Dataset creation
- Bulk ingestion
- Dataset retrieval
- Structured filtering
- Semantic retrieval
- Embedding/index management
- Dataset updates
- Dataset deletion
- Learning lifecycle
- Dataset statistics
"""

from __future__ import annotations

from typing import Any, Iterable

from .config import create_embedding_provider
from .dataset_item import DatasetItem
from .dataset_types import LearningStatus
from .embedding_provider import EmbeddingProvider
from .query_engine import DatasetQueryEngine
from .repository import DatasetRepository
from .semantic_retriever import SemanticRetriever
from .validator import DatasetValidator


class DatasetManager:
    """
    Main application service for OM Intelligence Dataset.
    """

    VERSION = "1.2.0"

    def __init__(
        self,
        repository: DatasetRepository | None = None,
        validator: DatasetValidator | None = None,
        query_engine: DatasetQueryEngine | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:

        self.repository = (
            repository
            or DatasetRepository()
        )

        self.validator = (
            validator
            or DatasetValidator()
        )

        if query_engine is not None:

            self.query_engine = query_engine

        else:

            provider = (
                embedding_provider
                or create_embedding_provider()
            )

            semantic_retriever = SemanticRetriever(
                repository=self.repository,
                embedding_provider=provider,
            )

            self.query_engine = DatasetQueryEngine(
                repository=self.repository,
                semantic_retriever=semantic_retriever,
            )

    # =========================================================
    # CREATE
    # =========================================================

    def add(
        self,
        item: DatasetItem,
    ) -> DatasetItem:

        validated = self.validator.validate(
            item
        )

        saved = self.repository.save(
            validated
        )

        self.query_engine.semantic_retriever.index_item(
            saved
        )

        return saved

    # =========================================================
    # BULK CREATE
    # =========================================================

    def add_many(
        self,
        items: Iterable[DatasetItem],
    ) -> int:

        count = 0

        for item in items:

            self.add(item)

            count += 1

        return count

    # =========================================================
    # GET
    # =========================================================

    def get(
        self,
        item_id: str,
    ) -> DatasetItem | None:

        if not item_id:

            return None

        return self.repository.get(
            item_id
        )

    # =========================================================
    # STRUCTURED SEARCH
    # =========================================================

    def find(
        self,
        *,
        intent: str | None = None,
        domain: str | None = None,
        language: str | None = None,
        dataset_type: str | None = None,
        min_quality: float = 0.0,
        limit: int = 20,
    ) -> list[DatasetItem]:

        return self.query_engine.find(
            intent=intent,
            domain=domain,
            language=language,
            dataset_type=dataset_type,
            min_quality=min_quality,
            limit=limit,
        )

    # =========================================================
    # SEMANTIC SEARCH
    # =========================================================

    def semantic_search(
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
    ):

        return self.query_engine.semantic_search(
            query,
            intent=intent,
            domain=domain,
            language=language,
            dataset_type=dataset_type,
            min_quality=min_quality,
            min_similarity=min_similarity,
            limit=limit,
        )

    # =========================================================
    # UPDATE
    # =========================================================

    def update(
        self,
        item: DatasetItem,
    ) -> DatasetItem:

        if not item.item_id:

            raise ValueError(
                "Cannot update dataset item without item_id."
            )

        existing = self.repository.get(
            item.item_id
        )

        if existing is None:

            raise KeyError(
                f"Dataset item not found: {item.item_id}"
            )

        validated = self.validator.validate(
            item
        )

        saved = self.repository.save(
            validated
        )

        self.query_engine.semantic_retriever.index_item(
            saved
        )

        return saved

    # =========================================================
    # DELETE
    # =========================================================

    def delete(
        self,
        item_id: str,
    ) -> bool:

        if not item_id:

            return False

        deleted = self.repository.delete(
            item_id
        )

        if deleted:

            self.query_engine.semantic_retriever.delete(
                item_id
            )

        return deleted

    # =========================================================
    # COUNT
    # =========================================================

    def count(self) -> int:

        return self.repository.count()

    # =========================================================
    # INDEX COUNT
    # =========================================================

    def indexed_count(self) -> int:

        return (
            self.query_engine
            .semantic_retriever
            .count_indexed()
        )

    # =========================================================
    # LEARNING STATUS
    # =========================================================

    def mark_learning_status(
        self,
        item_id: str,
        status: LearningStatus,
    ) -> DatasetItem:

        item = self.get(
            item_id
        )

        if item is None:

            raise KeyError(
                f"Dataset item not found: {item_id}"
            )

        item.learning_status = status

        return self.update(
            item
        )

    # =========================================================
    # APPROVE
    # =========================================================

    def approve(
        self,
        item_id: str,
    ) -> DatasetItem:

        return self.mark_learning_status(
            item_id,
            LearningStatus.APPROVED,
        )

    # =========================================================
    # REJECT
    # =========================================================

    def reject(
        self,
        item_id: str,
    ) -> DatasetItem:

        return self.mark_learning_status(
            item_id,
            LearningStatus.REJECTED,
        )

    # =========================================================
    # LEARNED
    # =========================================================

    def mark_learned(
        self,
        item_id: str,
    ) -> DatasetItem:

        return self.mark_learning_status(
            item_id,
            LearningStatus.LEARNED,
        )

    # =========================================================
    # VALIDATE
    # =========================================================

    def validate(
        self,
        item: DatasetItem,
    ) -> DatasetItem:

        return self.validator.validate(
            item
        )

    # =========================================================
    # STATISTICS
    # =========================================================

    def stats(self) -> dict[str, Any]:

        total_items = self.repository.count()

        indexed_items = self.indexed_count()

        retriever = (
            self.query_engine
            .semantic_retriever
        )

        return {
            "manager_version": self.VERSION,

            "total_items": total_items,

            "indexed_items": indexed_items,

            "unindexed_items": max(
                0,
                total_items - indexed_items,
            ),

            "semantic_search": True,

            "vector_search": True,

            "embedding_provider":
                retriever.model_name,

            "embedding_dimension":
                retriever
                .embedding_provider
                .dimension,

            "storage": "sqlite",

            "persistent": True,

            "dataset_ready":
                total_items > 0,

            "semantic_index_ready":
                indexed_items > 0,
        }
