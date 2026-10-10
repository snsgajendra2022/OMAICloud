"""
OM Intelligence Dataset Quality Scorer.
"""

from __future__ import annotations

from typing import Any


class DatasetQualityScorer:

    def score(
        self,
        record: dict[str, Any],
    ) -> float:

        score = 0.0

        input_text = str(
            record.get(
                "input_text",
                "",
            )
        ).strip()

        response = str(
            record.get(
                "ideal_response",
                "",
            )
        ).strip()

        meaning = str(
            record.get(
                "meaning",
                "",
            )
        ).strip()

        goal = str(
            record.get(
                "goal",
                "",
            )
        ).strip()

        reasoning = str(
            record.get(
                "reasoning_summary",
                "",
            )
        ).strip()

        verification = str(
            record.get(
                "verification_strategy",
                "",
            )
        ).strip()

        # Input quality
        if input_text:
            score += 0.20

        if len(input_text) >= 15:
            score += 0.05

        # Response quality
        if response:
            score += 0.20

        if len(response) >= 40:
            score += 0.05

        # Semantic metadata
        if meaning:
            score += 0.10

        if goal:
            score += 0.10

        # Reasoning
        if reasoning:
            score += 0.10

        # Verification
        if verification:
            score += 0.10

        return round(
            min(
                1.0,
                score,
            ),
            3,
        )

    def enrich(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:

        data = dict(record)

        calculated = self.score(
            data
        )

        existing = data.get(
            "quality_score"
        )

        if existing is None:

            data[
                "quality_score"
            ] = calculated

        else:

            data[
                "quality_score"
            ] = max(
                0.0,
                min(
                    1.0,
                    float(existing),
                ),
            )

        return data