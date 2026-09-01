from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RetrievalDecision:
    accepted: bool
    reason: str
    confidence: float


class RelevanceChecker:
    """
    Filters retrieved knowledge before sending it
    to the reasoning/response engine.
    """

    def __init__(
        self,
        min_score: float = 0.65
    ):
        self.min_score = min_score


    def check(
        self,
        query: str,
        result: Dict[str, Any],
        intent: Dict[str, Any] | None = None
    ) -> RetrievalDecision:

        score = float(
            result.get(
                "score",
                0
            )
        )

        if score < self.min_score:
            return RetrievalDecision(
                accepted=False,
                reason="Similarity score too low",
                confidence=score
            )


        result_domain = (
            result.get(
                "domain",
                ""
            )
            .lower()
        )


        if intent:

            expected_domain = (
                intent.get(
                    "domain",
                    ""
                )
                .lower()
            )

            if (
                expected_domain
                and
                result_domain
                and
                expected_domain != result_domain
            ):
                return RetrievalDecision(
                    accepted=False,
                    reason="Domain mismatch",
                    confidence=score
                )


        return RetrievalDecision(
            accepted=True,
            reason="Knowledge is relevant",
            confidence=score
        )