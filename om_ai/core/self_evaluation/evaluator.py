from __future__ import annotations


from .evaluation_metrics import (
    EvaluationMetrics
)



class ResponseEvaluator:
    """
    Evaluates OM generated output.
    """


    def __init__(self):

        self.metrics = EvaluationMetrics()



    def evaluate(
        self,
        answer: str,
        expected: str | None = None
    ):


        metrics = (
            self.metrics.calculate(
                answer,
                expected
            )
        )


        score = sum(
            metrics.values()
        ) / len(metrics)



        return score, metrics