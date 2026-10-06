"""
OM Intelligence Dataset Index.

Provides lightweight metadata indexes for fast filtering.

Semantic/vector retrieval will be added in a later step.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .dataset_item import DatasetItem


class DatasetIndex:

    def __init__(self) -> None:

        self.by_intent: dict[
            str,
            set[str]
        ] = defaultdict(set)

        self.by_domain: dict[
            str,
            set[str]
        ] = defaultdict(set)

        self.by_type: dict[
            str,
            set[str]
        ] = defaultdict(set)

        self.by_language: dict[
            str,
            set[str]
        ] = defaultdict(set)

        self.by_tag: dict[
            str,
            set[str]
        ] = defaultdict(set)

    # ---------------------------------------------------------
    # Add
    # ---------------------------------------------------------

    def add(
        self,
        item: DatasetItem,
    ) -> None:

        self.by_intent[
            item.intent
        ].add(
            item.item_id
        )

        self.by_domain[
            item.domain
        ].add(
            item.item_id
        )

        self.by_type[
            item.dataset_type.value
        ].add(
            item.item_id
        )

        self.by_language[
            item.language
        ].add(
            item.item_id
        )

        for tag in item.tags:

            self.by_tag[
                tag.lower()
            ].add(
                item.item_id
            )

    # ---------------------------------------------------------
    # Bulk
    # ---------------------------------------------------------

    def add_many(
        self,
        items: Iterable[DatasetItem],
    ) -> None:

        for item in items:
            self.add(item)

    # ---------------------------------------------------------
    # Query
    # ---------------------------------------------------------

    def ids_for_intent(
        self,
        intent: str,
    ) -> set[str]:

        return set(
            self.by_intent.get(
                intent,
                set(),
            )
        )

    def ids_for_domain(
        self,
        domain: str,
    ) -> set[str]:

        return set(
            self.by_domain.get(
                domain,
                set(),
            )
        )

    def ids_for_type(
        self,
        dataset_type: str,
    ) -> set[str]:

        return set(
            self.by_type.get(
                dataset_type,
                set(),
            )
        )

    def ids_for_language(
        self,
        language: str,
    ) -> set[str]:

        return set(
            self.by_language.get(
                language,
                set(),
            )
        )

    def ids_for_tag(
        self,
        tag: str,
    ) -> set[str]:

        return set(
            self.by_tag.get(
                tag.lower(),
                set(),
            )
        )