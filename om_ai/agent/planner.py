"""Lightweight planner for chat Agent Brain (wraps RulePlanner)."""
from __future__ import annotations

from om_ai.reasoning.planner import Plan, PlanStep, RulePlanner


def plan_for_goal(goal: str, *, max_steps: int = 6) -> Plan:
    """Create a deterministic multi-step plan for assistant-style goals."""
    available = [
        "knowledge.search",
        "discovery.openapi",
        "action.shell",
        "discovery.project",
    ]
    return RulePlanner().create(goal, available, max_steps=max_steps)


def plan_as_bullets(plan: Plan) -> list[str]:
    bullets: list[str] = []
    for i, step in enumerate(plan.steps, start=1):
        tool = f" [{step.tool}]" if step.tool else ""
        bullets.append(f"{i}. {step.description}{tool}")
    return bullets


def coding_plan(goal: str) -> list[str]:
    """Structured coding assistant outline when the base model is too small."""
    g = (goal or "").strip() or "the coding task"
    return [
        f"Clarify the goal: {g[:120]}",
        "Locate the relevant files / stack (frontend, backend, config).",
        "Identify the failure mode or missing piece.",
        "Propose a minimal fix or implementation.",
        "List how to verify (tests, curl, UI check).",
    ]


__all__ = ["Plan", "PlanStep", "plan_for_goal", "plan_as_bullets", "coding_plan"]
