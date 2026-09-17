from __future__ import annotations



class ImprovementFeedback:
    """
    Creates learning suggestions.
    """



    def generate(
        self,
        failures: list[str]
    ):


        recommendations=[]


        for failure in failures:


            recommendations.append(

                f"Create additional training data for: {failure}"

            )


        return recommendations