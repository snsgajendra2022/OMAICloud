from __future__ import annotations


from .evaluator import (
    ResponseEvaluator
)

from .failure_analyzer import (
    FailureAnalyzer
)

from .improvement_feedback import (
    ImprovementFeedback
)

from .evaluation_memory import (
    EvaluationMemory
)

from .evaluation_result import (
    EvaluationResult
)



class SelfEvaluationEngine:
    """
    OM Self Evaluation Brain.

    Responsible for:

    - checking responses
    - detecting failures
    - creating improvement tasks
    """



    def __init__(self):

        self.evaluator = (
            ResponseEvaluator()
        )

        self.failure_analyzer = (
            FailureAnalyzer()
        )

        self.feedback = (
            ImprovementFeedback()
        )

        self.memory = (
            EvaluationMemory()
        )



    def evaluate(
        self,
        answer: str,
        expected: str | None = None
    ):


        score, metrics = (
            self.evaluator.evaluate(
                answer,
                expected
            )
        )


        failures = (
            self.failure_analyzer.analyze(
                score,
                metrics
            )
        )


        recommendations = (
            self.feedback.generate(
                failures
            )
        )


        result = EvaluationResult(

            score=score,

            passed=score >= 0.7,

            weaknesses=failures,

            recommendations=recommendations,

            metadata={

                "metrics":
                    metrics

            }

        )


        self.memory.store(
            result
        )


        return result