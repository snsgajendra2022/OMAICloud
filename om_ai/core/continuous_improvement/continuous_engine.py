from __future__ import annotations


from .weakness_analyzer import (
    WeaknessAnalyzer
)

from .improvement_strategy import (
    ImprovementStrategy
)

from .improvement_planner import (
    ImprovementPlanner
)

from .improvement_tracker import (
    ImprovementTracker
)

from .cycle_manager import (
    ImprovementCycleManager
)

from .improvement_event import (
    ImprovementEvent
)

from om_ai.core.training_intelligence import (
    TrainingIntelligenceEngine
)

from om_ai.core.checkpoint_intelligence import (
    Checkpoint,
    CheckpointManager
)

class ContinuousImprovementEngine:
    """
    OM Continuous Improvement Brain.
    """


    def __init__(self):

        self.analyzer = WeaknessAnalyzer()

        self.strategy = ImprovementStrategy()

        self.planner = ImprovementPlanner()

        self.tracker = ImprovementTracker()

        self.cycles = ImprovementCycleManager()

        self.training_engine = TrainingIntelligenceEngine()

        self.checkpoint_manager = CheckpointManager()



    def observe(
        self,
        capability: str,
        score: float,
        issue: str
    ):


        severity = self.analyzer.analyze(
            score
        )


        event = ImprovementEvent(

            capability=capability,

            score=score,

            issue=issue

        )


        self.tracker.add(
            event
        )


        actions = self.strategy.create(

            capability,

            severity

        )


        plan = self.planner.plan(

            capability,

            actions

        )


        cycle = self.cycles.start(
            plan
        )

        training = self.training_engine.create_training(

                capability="reasoning",

                score=0.42

            )
            
        checkpoint = Checkpoint(

            version="OM-1.1",

            path="checkpoints/om-1.1",

            score=0.82

        )


        result = self.checkpoint_manager.process(
            checkpoint
        )

        return {

            "event": event,

            "severity": severity,

            "plan": plan,

            "cycle": cycle,

            "training": training,

            "checkpoint": result

        }