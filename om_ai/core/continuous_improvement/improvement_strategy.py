from __future__ import annotations



class ImprovementStrategy:

    """
    Decides improvement action.
    """


    def create(
        self,
        capability,
        severity
    ):


        if severity == "critical":

            return [

                "collect knowledge",

                "generate curriculum",

                "create training dataset",

                "evaluate again"

            ]


        if severity == "needs_improvement":

            return [

                "create additional examples",

                "run targeted evaluation"

            ]


        return [

            "continue monitoring"

        ]