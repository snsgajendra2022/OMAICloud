"""OM Reasoning Engine — deep chain with STEP 88 advanced reasoning."""
from __future__ import annotations

from typing import Any

from .problem_analyzer import ProblemAnalyzer
from .solution_planner import SolutionPlanner
from .chain_reasoner import ChainReasoner


class AdvancedReasoningEngine:
    def __init__(self) -> None:
        self.analyzer = ProblemAnalyzer()
        self.planner = SolutionPlanner()
        self.reasoner = ChainReasoner()

    def process(self, user_input: str, message: str | None = None) -> dict[str, Any]:
        text = (message or user_input or "").strip()
        analysis = self.analyzer.analyze(user_input or text, text)
        plan = self.planner.create(analysis)
        reasoning = self.reasoner.reason(analysis, plan)

        deep: dict[str, Any] = {}
        try:
            from om_ai.core.steps.step88_advanced_reasoning import (
                AdvancedReasoningIntelligence,
            )

            deep = AdvancedReasoningIntelligence().reason(text)
            if deep.get("plan"):
                plan = list(dict.fromkeys(list(plan or []) + list(deep["plan"])))
        except Exception as exc:
            deep = {"error": str(exc)}

        return {
            "analysis": analysis,
            "plan": plan,
            "reasoning": reasoning,
            "deep": deep,
            "verification": deep.get("verification"),
            "final_reasoning": deep.get("final_reasoning"),
            "status": "reasoning_completed",
        }


# Backward-compatible alias used by brain_pipeline / older callers.
ReasoningEngine = AdvancedReasoningEngine

