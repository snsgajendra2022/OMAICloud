"""Solution planner — ordered solve steps from analysis + hypotheses."""
from __future__ import annotations

from typing import Any


class SolutionPlanner:
    """Plan the solve path before reasoning / explanation."""

    def plan(
        self,
        *,
        analysis: dict[str, Any] | None = None,
        hypotheses: dict[str, Any] | None = None,
        answer_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        analysis = dict(analysis or {})
        hypotheses = dict(hypotheses or {})
        answer_plan = dict(answer_plan or {})
        ptype = str(analysis.get("problem_type") or "general")
        missing = list(analysis.get("missing_information") or [])
        top = hypotheses.get("top") or {}

        steps: list[str]
        if ptype == "debugging":
            steps = [
                "restate_likely_cause",
                "list_quick_checks",
                "propose_fix_order",
                "verify_after_each_change",
            ]
            if missing:
                steps.insert(1, "ask_for_missing_signal")
        elif ptype == "coding":
            steps = ["clarify_io", "minimal_implementation", "edge_cases", "test_plan"]
        elif ptype == "howto":
            steps = ["define_success", "prerequisites", "ordered_steps", "verify"]
        elif ptype == "comparison":
            steps = ["criteria", "option_tradeoffs", "recommendation"]
        elif ptype == "explanation":
            steps = ["define", "why", "example", "optional_deeper_dive"]
        else:
            steps = list(answer_plan.get("steps") or ["understand", "answer", "next_step"])

        return {
            "problem_type": ptype,
            "steps": steps,
            "leading_hypothesis": top.get("claim") or "",
            "ask_details": bool(missing) or bool(answer_plan.get("ask_details")),
            "missing_information": missing,
            "style": str(answer_plan.get("style") or "structured"),
            "domain": str(analysis.get("domain") or "general"),
        }
