from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImprovementEvent:
    """
    Represents one improvement signal.
    """

    capability: str

    score: float

    issue: str

    source: str = "evaluation"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )