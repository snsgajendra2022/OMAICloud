from __future__ import annotations


from .learning_gap import LearningGap



class GapDetector:
    """
    Detect missing OM capabilities.
    """



    def analyze(
        self,
        capability: str,
        score: float,
        feedback: str | None = None
    ):


        gaps = []


        if score < 0.5:


            gaps.append(

                LearningGap(

                    area=capability,

                    reason=(
                        "Low capability score"
                    ),

                    severity=(
                        1 - score
                    ),

                    evidence=[

                        feedback
                        or
                        "Low evaluation score"

                    ],

                    suggested_learning=[

                        f"Study {capability}",

                        f"Practice {capability}",

                        f"Generate examples for {capability}"

                    ]

                )

            )


        return gaps