from __future__ import annotations



class ImprovementPlanner:
    """
    Converts gaps into learning plans.
    """



    def create_plan(
        self,
        gap
    ):


        return {

            "target":

                gap.area,


            "priority":

                gap.severity,


            "steps":[

                "collect knowledge",

                "generate training examples",

                "evaluate improvement",

                "update capability score"

            ]

        }