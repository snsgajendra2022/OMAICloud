from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KnowledgeEdge:
    """
    Relationship between two concepts.
    """


    source: str

    target: str

    relationship: str

    weight: float = 1.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    def to_dict(self):

        return {

            "source": self.source,

            "target": self.target,

            "relationship": self.relationship,

            "weight": self.weight,

            "metadata": self.metadata,

        }