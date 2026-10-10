"""
OM Intelligence Dataset Manager.

Application service responsible for dataset lifecycle operations.
"""

from __future__ import annotations

from typing import Any, Iterable

from .dataset_item import DatasetItem
from .dataset_types import LearningStatus
from .repository import DatasetRepository
from .query_engine import DatasetQueryEngine


class DatasetManager:

    def __init__(
        self,
        repository: DatasetRepository | None = None,
    ) -> None:

        self.repository = (
            repository
            or DatasetRepository()
        )

        self.query = DatasetQueryEngine(
            repository=self.repository
        )

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def add(
        self,
        item: DatasetItem,
    ) -> DatasetItem:

        return self.repository.save(
            item
        )

    # ---------------------------------------------------------
    # Bulk create
    # ---------------------------------------------------------

    def add_many(
        self,
        items: Iterable[DatasetItem],
    ) -> int:

        return self.repository.save_many(
            items
        )

    # ---------------------------------------------------------
    # Retrieve
    # ---------------------------------------------------------

    def get(
        self,
        item_id: str,
    ) -> DatasetItem | None:

        return self.repository.get(
            item_id
        )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def find(
        self,
        **filters: Any,
    ) -> list[DatasetItem]:

        return self.query.find(
            **filters
        )

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete(
        self,
        item_id: str,
    ) -> bool:

        return self.repository.delete(
            item_id
        )

    # ---------------------------------------------------------
    # Stats
    # ---------------------------------------------------------

    def count(self) -> int:

        return self.repository.count()