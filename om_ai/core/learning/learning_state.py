"""STEP 83 core LearningState."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LearningState:
    success: bool = False
    score: float = 0.0
    mistakes: list[Any] = field(default_factory=list)
    improvements: list[Any] = field(default_factory=list)
    experiences: list[Any] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    total_experiences: int = 0

    def add_experience(self, item: Any = None) -> None:
        self.total_experiences += 1
        if item is not None:
            self.experiences.append(item)

    def add_improvement(self, item: Any = None) -> None:
        if item is not None:
            self.improvements.append(item)
