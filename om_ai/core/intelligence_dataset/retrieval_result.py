"""
OM Intelligence Retrieval Result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .dataset_item import DatasetItem


@dataclass(slots=True)
class RetrievalResult:
    """
    One semantic retrieval result.
    """

    item: DatasetItem

    similarity: float

    rank: int

    retrieval_reason: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def item_id(self) -> str:

        return self.item.item_id

    @property
    def input_text(self) -> str:

        return self.item.input_text

    def to_dict(self) -> dict[str, Any]:

        return {

            "item_id":
                self.item.item_id,

            "input_text":
                self.item.input_text,

            "ideal_response":
                self.item.ideal_response,

            "similarity":
                round(
                    self.similarity,
                    6,
                ),

            "rank":
                self.rank,

            "retrieval_reason":
                self.retrieval_reason,

            "metadata":
                self.metadata,
        }