from __future__ import annotations


class ComplexityScoringEngine:
    """
    Calculates final complexity.

    No fixed question database.
    """


    def calculate(
        self,
        scores: dict[str, float]
    ):


        weights = {

            "knowledge_depth": 0.20,

            "reasoning_depth": 0.25,

            "coding_complexity": 0.15,

            "abstraction_level": 0.15,

            "dependency_depth": 0.10,

            "architecture_complexity": 0.15,

        }


        total = 0


        for key, weight in weights.items():

            total += (

                scores.get(
                    key,
                    0
                )

                *

                weight

            )


        return round(
            total,
            2
        )



    def classify(
        self,
        score: float
    ):


        if score < 25:

            return "foundation"


        if score < 50:

            return "intermediate"


        if score < 75:

            return "advanced"


        if score < 90:

            return "expert"


        return "research"