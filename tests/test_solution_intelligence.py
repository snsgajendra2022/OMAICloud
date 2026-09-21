"""Tests for GPT-style chat_intelligence solution stack."""
from __future__ import annotations

from om_ai.core.chat_intelligence import (
    SolutionEngine,
    ProblemAnalyzer,
    HypothesisEngine,
    SolutionPlanner,
    ReasoningEngine,
    VerificationEngine,
    ExplanationEngine,
    SolutionMemory,
)


def test_problem_analyzer_debug_domain():
    pa = ProblemAnalyzer()
    pack = pa.analyze("React blank page after deploy", plan={"strategy": "technical_solution"})
    assert pack["problem_type"] == "debugging"
    assert pack["domain"] == "frontend"
    assert pack["goal"]


def test_full_solution_pipeline_debugging():
    engine = SolutionEngine()
    out = engine.solve(
        "My React app shows a blank page",
        plan={"strategy": "technical_solution", "ask_details": True},
        context={},
    )
    assert out.get("solved") is True
    assert out.get("answer")
    assert "check" in (out.get("answer") or "").lower() or out.get("checks")
    assert out.get("analysis", {}).get("problem_type") == "debugging"
    assert out.get("hypotheses", {}).get("top")
    assert out.get("reasoning", {}).get("fix_order")
    assert out.get("verification", {}).get("score", 0) > 0.4
    assert out.get("confidence", 0) > 0.4


def test_solution_memory_recall():
    mem = SolutionMemory()
    analysis = {"problem_type": "debugging", "domain": "frontend"}
    mem.store(
        message="React blank page",
        analysis=analysis,
        solution={"solved": True, "kind": "debugging", "answer": "Check console"},
        confidence=0.8,
    )
    hits = mem.recall("blank page in react", analysis=analysis)
    assert hits
    assert hits[0]["problem_type"] == "debugging"


def test_components_compose():
    analysis = ProblemAnalyzer().analyze("how to deploy fastapi", plan={"strategy": "step_by_step"})
    hyps = HypothesisEngine().generate("how to deploy fastapi", analysis=analysis)
    plan = SolutionPlanner().plan(analysis=analysis, hypotheses=hyps, answer_plan={"strategy": "step_by_step"})
    reasoning = ReasoningEngine().reason("how to deploy fastapi", analysis=analysis, hypotheses=hyps, plan=plan)
    explained = ExplanationEngine().explain(
        "how to deploy fastapi", analysis=analysis, reasoning=reasoning, plan=plan
    )
    verified = VerificationEngine().verify(
        explained["answer"], message="how to deploy fastapi", analysis=analysis, reasoning=reasoning
    )
    assert plan["steps"]
    assert explained["answer"]
    assert "ok" in verified
