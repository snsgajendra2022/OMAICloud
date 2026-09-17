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


        return {

            "event": event,

            "severity": severity,

            "plan": plan,

            "cycle": cycle

        }