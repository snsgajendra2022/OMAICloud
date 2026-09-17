from __future__ import annotations



class FailureAnalyzer:
    """
    Finds why OM failed.
    """



    def analyze(
        self,
        score: float,
        metrics: dict
    ):


        problems=[]


        if metrics.get(
            "completeness",
            0
        ) < 0.5:

            problems.append(
                "Insufficient explanation"
            )


        if metrics.get(
            "relevance",
            0
        ) < 0.5:

            problems.append(
                "Low relevance"
            )


        if score < 0.5:

            problems.append(
                "Capability improvement required"
            )


        return problems