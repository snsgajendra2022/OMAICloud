from __future__ import annotations


from .learning_state import LearningState

from .gap_detector import GapDetector

from .improvement_planner import ImprovementPlanner

from .learning_memory import LearningMemory



class AdaptiveLearningEngine:
    """
    OM Adaptive Learning Intelligence.

    Finds weaknesses and creates
    improvement paths.
    """



    def __init__(self):

        self.states = {}

        self.detector = GapDetector()

        self.planner = ImprovementPlanner()

        self.memory = LearningMemory()



    def observe(
        self,
        capability: str,
        success: bool,
        score: float,
        feedback: str | None = None
    ):


        if capability not in self.states:


            self.states[capability] = LearningState(

                capability=capability

            )



        state = self.states[capability]


        state.update(

            success,

            score

        )


        gaps = self.detector.analyze(

            capability,

            score,

            feedback

        )


        plans = [

            self.planner.create_plan(
                gap
            )

            for gap in gaps

        ]


        record = {

            "capability":

                capability,


            "state":

                state,


            "gaps":

                gaps,


            "plans":

                plans

        }


        self.memory.add(
            record
        )


        return record