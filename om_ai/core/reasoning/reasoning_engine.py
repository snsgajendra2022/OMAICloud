"""OM Reasoning Engine — analyze → plan → chain reason."""
from __future__ import annotations

from typing import Any

from .problem_analyzer import ProblemAnalyzer
from .solution_planner import SolutionPlanner
from .chain_reasoner import ChainReasoner
from .critic import Critic
from .verifier import Verifier


class ReasoningEngine:
    def __init__(self) -> None:
        self.analyzer = ProblemAnalyzer()
        self.planner = SolutionPlanner()
        self.reasoner = ChainReasoner()
        self.critic = Critic()
        self.verifier = Verifier()

    def process(self, user_input: str, message: str | None = None) -> dict[str, Any]:
        text = (message or user_input or "").strip()
        analysis = self.analyzer.analyze(user_input or text, text)
        plan = self.planner.create(analysis)
        reasoning = self.reasoner.reason(analysis, plan)
        return {
            "analysis": analysis,
            "plan": plan,
            "reasoning": reasoning,
            "status": "reasoning_completed",
        }
