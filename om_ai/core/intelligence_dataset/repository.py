"""
OM Intelligence Dataset Repository.

Validated application-level access to persistent dataset storage.
"""

from __future__ import annotations

from typing import Any, Iterable

from .dataset_item import DatasetItem
from .dataset_store import DatasetStore
from .validator import DatasetValidator


class DatasetRepository:
    """High-level CRUD repository."""

    def __init__(
        self,
        store: DatasetStore | None = None,
        validator: DatasetValidator | None = None,
    ) -> None:

        self.store = (
            store
            or DatasetStore()
        )

        self.validator = (
            validator
            or DatasetValidator()
        )

    # ---------------------------------------------------------
    # Create / update
    # ---------------------------------------------------------

    def save(
        self,
        item: DatasetItem,
    ) -> DatasetItem:

        validated = self.validator.validate(
            item
        )

        return self.store.save(
            validated
        )

    def save_many(
        self,
        items: Iterable[DatasetItem],
    ) -> int:

        count = 0

        for item in items:

            self.save(item)

            count += 1

        return count

    # ---------------------------------------------------------
    # Read
    # ---------------------------------------------------------

    def get(
        self,
        item_id: str,
    ) -> DatasetItem | None:

        return self.store.get(
            item_id
        )

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete(
        self,
        item_id: str,
    ) -> bool:

        return self.store.delete(
            item_id
        )

    # ---------------------------------------------------------
    # Count
    # ---------------------------------------------------------

    def count(self) -> int:

        return self.store.count()