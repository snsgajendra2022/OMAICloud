from __future__ import annotations

from typing import Any

from .brain_context import BrainContext
from .decision_engine import DecisionEngine
from .task_planner import TaskPlanner


class OMBrianOrchestrator:
    """
    Brain module orchestrator.

    Registers STEP 24 / STEP 26 and domain modules, then runs a plan.
    """

    def __init__(self) -> None:
        self.decision = DecisionEngine()
        self.planner = TaskPlanner()
        self.modules: dict[str, Any] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        # Lazy callables so import cost stays low until used.
        def _step24(ctx: BrainContext):
            from om_ai.core.brain_router import run_om_brain_router

            return run_om_brain_router(ctx.user_input)

        def _step26(ctx: BrainContext):
            from om_ai.core.agent_runtime import run_agent_runtime

            return run_agent_runtime(ctx.user_input)

        def _research(ctx: BrainContext):
            from om_ai.core.brain_router.deep_research_factory import (
                build_deep_research_engine,
            )

            return build_deep_research_engine().research(ctx.user_input)

        def _knowledge(ctx: BrainContext):
            from om_ai.core.knowledge_brain import KnowledgeBrain

            return KnowledgeBrain().analyze(ctx.user_input)

        self.register_module("step24", _step24)
        self.register_module("step26", _step26)
        self.register_module("agents", _step26)
        self.register_module("research", _research)
        self.register_module("knowledge", _knowledge)

    def register_module(self, name, module) -> None:
        self.modules[name] = module

    def process(self, message: str):
        context = BrainContext(user_input=message)
        context = self.decision.decide(context)
        plan = self.planner.create_plan(context)

        # Always include STEP 24 + STEP 26 in the production plan.
        ordered = []
        for step in ("step24", "step26"):
            if step not in plan:
                ordered.append(step)
        for step in plan:
            if step not in ordered:
                ordered.append(step)

        results = {}
        for step in ordered:
            # Avoid double-running STEP 26 when STEP 24 already nested it.
            if step == "step26" and isinstance(results.get("step24"), dict):
                nested = ((results.get("step24") or {}).get("meta") or {}).get("step26")
                if isinstance(nested, dict) and nested:
                    results[step] = {
                        "goal": nested.get("goal"),
                        "agents": list(nested.get("agents") or []),
                        "meta": {"step": 26, "source": "step24"},
                        "stages": ["agent_runtime", "from_step24"],
                    }
                    continue
            module = self.modules.get(step)
            if module:
                results[step] = module(context)

        # Surface agent list on context when STEP 26 ran.
        step26 = results.get("step26")
        if isinstance(step26, dict):
            context.agents = list(step26.get("agents") or [])

        return {
            "context": context,
            "plan": ordered,
            "results": results,
        }


# Correct spelling alias
OMBrainOrchestrator = OMBrianOrchestrator
