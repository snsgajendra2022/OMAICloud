from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class LearningGap:
    """
    Represents missing capability.
    """


    area: str


    reason: str


    severity: float


    evidence: list[str] = field(
        default_factory=list
    )


    suggested_learning: list[str] = field(
        default_factory=list
    )