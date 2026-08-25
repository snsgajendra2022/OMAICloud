"""Full reasoning pipeline used by API + CLI."""
from __future__ import annotations

from typing import Any

from .analyzer import IntentAnalyzer
from .planner import PlanningEngine
from .solver import SolutionGenerator
from .verifier import VerificationEngine
from .reflection import ReflectionEngine


def run_reasoning_pipeline(
    question: str,
    *,
    knowledge_hits: list[str] | None = None,
) -> dict[str, Any]:
    intent = IntentAnalyzer().analyze(question)
    plan = PlanningEngine().plan(intent)
    solution = SolutionGenerator().solve(
        question, intent, plan, knowledge_hits=knowledge_hits
    )
    verify = VerificationEngine().verify(intent, solution)
    reflection = ReflectionEngine().reflect(verify, domain=intent.domain)
    return {
        "understanding": intent.understanding,
        "intent": intent.to_dict(),
        "plan": plan.plan,
        "agents": plan.agents,
        "solution": solution.solution,
        "architecture": solution.architecture,
        "validation": verify.validation,
        "passed": verify.passed,
        "score": verify.score,
        "critique": reflection.critique,
        "weak_areas": reflection.weak_areas,
        "training_hints": reflection.training_hints,
        "meta": {
            "pipeline": "om-foundation-reasoning-v1",
            "knowledge_hits": len(knowledge_hits or []),
        },
    }
