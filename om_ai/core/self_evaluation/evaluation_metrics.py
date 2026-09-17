from __future__ import annotations


class EvaluationMetrics:
    """
    Calculates response quality dimensions.
    """


    def calculate(
        self,
        answer: str,
        expected: str | None = None
    ):


        length_score = min(
            len(answer) / 500,
            1
        )


        completeness = (
            1
            if len(answer.strip()) > 50
            else 0.5
        )


        relevance = 1.0


        if expected:

            if expected.lower() in answer.lower():

                relevance = 1.0

            else:

                relevance = 0.5



        return {

            "length_quality":
                length_score,

            "completeness":
                completeness,

            "relevance":
                relevance,

        }