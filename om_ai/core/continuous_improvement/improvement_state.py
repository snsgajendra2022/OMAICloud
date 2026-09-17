from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ImprovementState:

    capability: str

    current_score: float = 0.0

    target_score: float = 0.9

    improvement_count: int = 0

    history: list = field(
        default_factory=list
    )


    def update(
        self,
        score: float
    ):

        self.current_score = score

        self.improvement_count += 1

        self.history.append(
            {
                "score": score
            }
        )