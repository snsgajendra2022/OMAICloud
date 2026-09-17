from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DatasetItem:
    """
    Represents one training sample.
    """

    instruction: str

    output: str

    dataset_type: str = "sft"

    domain: str = "general"

    quality_score: float = 0.0

    difficulty_score: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    def to_dict(self):

        return {

            "instruction": self.instruction,

            "output": self.output,

            "dataset_type": self.dataset_type,

            "domain": self.domain,

            "quality_score": self.quality_score,

            "difficulty_score": self.difficulty_score,

            "metadata": self.metadata,

        }