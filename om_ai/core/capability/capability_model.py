from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilityScore:
    """
    Represents one OM capability.
    """

    name: str

    score: float = 0.0

    confidence: float = 0.0

    evaluations: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    def update(
        self,
        score: float
    ):

        self.evaluations += 1


        self.score = (

            self.score * 0.7

            +

            score * 0.3

        )


        self.confidence = min(
            self.evaluations / 100,
            1.0
        )