from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



@dataclass
class LearningState:
    """
    Current OM learning status.
    """


    capability: str


    score: float = 0.0


    confidence: float = 0.0


    attempts: int = 0


    successes: int = 0


    failures: int = 0


    metadata: dict[str, Any] = field(
        default_factory=dict
    )



    def update(
        self,
        success: bool,
        score: float
    ):

        self.attempts += 1


        if success:

            self.successes += 1

        else:

            self.failures += 1



        self.score = (

            self.score * 0.7

            +

            score * 0.3

        )


        self.confidence = (

            self.successes /

            max(
                self.attempts,
                1
            )

        )