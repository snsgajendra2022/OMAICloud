from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationResult:
    """
    Result of OM self evaluation.
    """


    score: float


    passed: bool


    strengths: list[str] = field(
        default_factory=list
    )


    weaknesses: list[str] = field(
        default_factory=list
    )


    recommendations: list[str] = field(
        default_factory=list
    )


    metadata: dict[str, Any] = field(
        default_factory=dict
    )