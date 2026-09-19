from __future__ import annotations
from typing import Any
from .executor import Executor
from .goal_parser import GoalParser
from .planner import Planner
from .recovery import Recovery
from .verifier import Verifier

_RT = None

class AutonomousAgentRuntime:
    def __init__(self) -> None:
        self.parser = GoalParser()
        self.planner = Planner()
        self.executor = Executor()
        self.verifier = Verifier()
        self.recovery = Recovery()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 57, "name": "Autonomous Agent Brain"}

    def run(self, text: str, *, actions=None, execute: bool = False) -> dict[str, Any]:
        goal = self.parser.parse(text)
        plan = self.planner.plan(goal)
        results = []
        if execute:
            for step in plan.get("steps") or []:
                r = self.executor.run_step(step, actions=actions)
                if not r.get("ok"):
                    r["recovery"] = self.recovery.recover(step, str(r.get("error") or ""))
                results.append(r)
        verify = self.verifier.check(results) if results else {"ok": False, "planned_only": True}
        return {"goal": goal, "plan": plan, "results": results, "verify": verify}


def get_autonomous_agent() -> AutonomousAgentRuntime:
    global _RT
    if _RT is None:
        _RT = AutonomousAgentRuntime()
    return _RT
