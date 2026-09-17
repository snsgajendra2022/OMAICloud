from __future__ import annotations


from .complexity_model import ComplexityScore

from .complexity_analyzer import ComplexityAnalyzer

from .scoring_engine import ComplexityScoringEngine



class DifficultyEngine:
    """
    OM Dynamic Difficulty Intelligence.
    """



    def __init__(self):

        self.analyzer = (
            ComplexityAnalyzer()
        )

        self.scorer = (
            ComplexityScoringEngine()
        )



    def evaluate(
        self,
        text: str
    ):


        dimensions = (
            self.analyzer
            .analyze_text(
                text
            )
        )


        overall = (
            self.scorer
            .calculate(
                dimensions
            )
        )


        level = (
            self.scorer
            .classify(
                overall
            )
        )


        return ComplexityScore(

            **dimensions,

            overall_score=overall,

            level=level

        )