from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



@dataclass
class ComplexityScore:
    """
    Represents intelligence difficulty.

    All values are dynamic scores.
    """


    knowledge_depth: float = 0.0

    reasoning_depth: float = 0.0

    coding_complexity: float = 0.0

    abstraction_level: float = 0.0

    dependency_depth: float = 0.0

    architecture_complexity: float = 0.0


    overall_score: float = 0.0


    level: str = "unknown"


    metadata: dict[str, Any] = field(
        default_factory=dict
    )