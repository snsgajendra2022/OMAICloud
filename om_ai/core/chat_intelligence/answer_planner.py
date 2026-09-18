"""Answer planner — decide how to structure the reply."""
from __future__ import annotations

from typing import Any

from .intent_understanding import IntentResult


class AnswerPlanner:
    """Choose answer strategy and ordered steps before generation."""

    STRATEGY_PLANS: dict[str, list[str]] = {
        "friendly_conversation": ["acknowledge", "offer_help"],
        "friendly_identity": ["introduce", "offer_help"],
        "technical_solution": [
            "understand_error",
            "ask_missing_details",
            "suggest_checks",
            "provide_fix",
        ],
        "code_solution": [
            "clarify_goal",
            "outline_approach",
            "provide_code_or_steps",
            "verify",
        ],
        "step_by_step": ["goal", "steps", "tips"],
        "explanation": ["define", "why_it_matters", "example"],
        "comparison": ["criteria", "option_a", "option_b", "recommendation"],
        "direct_answer": ["answer", "brief_context"],
        "contextual_continue": ["use_prior_context", "answer"],
        "general_assist": ["understand", "answer", "next_step"],
        "ask_clarify": ["ask_one_question"],
    }

    def plan(
        self,
        message: str,
        intent: IntentResult | dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if isinstance(intent, IntentResult):
            intent_d = intent.to_dict()
            strategy = intent.strategy
            needs_details = intent.needs_details
            domain = intent.domain
        else:
            intent_d = dict(intent or {})
            strategy = str(intent_d.get("strategy") or "general_assist")
            needs_details = bool(intent_d.get("needs_details"))
            domain = str(intent_d.get("domain") or "general")

        steps = list(self.STRATEGY_PLANS.get(strategy) or self.STRATEGY_PLANS["general_assist"])
        if needs_details and "ask_missing_details" not in steps:
            steps.insert(1, "ask_missing_details")

        style = "short"
        if strategy in {"technical_solution", "code_solution", "step_by_step", "comparison"}:
            style = "structured"
        elif strategy in {"explanation"}:
            style = "explanatory"

        return {
            "strategy": strategy,
            "style": style,
            "domain": domain,
            "steps": steps,
            "intent": intent_d,
            "use_context": bool((context or {}).get("context_blob")),
            "ask_details": needs_details,
            "guidance": self._guidance(strategy, message),
        }

    def _guidance(self, strategy: str, message: str) -> str:
        q = (message or "").strip()[:200]
        if strategy == "technical_solution":
            return (
                f"Troubleshoot: {q}. "
                "1) Restate likely cause 2) List 3–5 checks 3) Give a concrete fix "
                "4) Ask for console/error text if missing."
            )
        if strategy == "code_solution":
            return f"Provide a practical coding solution for: {q}"
        if strategy == "step_by_step":
            return f"Give numbered steps for: {q}"
        if strategy == "comparison":
            return f"Compare options clearly for: {q}"
        if strategy == "explanation":
            return f"Explain clearly in plain language: {q}"
        return f"Answer helpfully: {q}"
