from __future__ import annotations


class WeaknessAnalyzer:
    """
    Finds capability weaknesses.
    """


    def analyze(
        self,
        score: float
    ):

        if score < 0.5:

            return "critical"


        if score < 0.75:

            return "needs_improvement"


        return "healthy"