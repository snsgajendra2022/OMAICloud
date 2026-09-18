"""STEP 27 — Response Intelligence Upgrade orchestrator."""
from __future__ import annotations

from typing import Any

from .answer_improvement import AnswerImprovement
from .answer_structure import AnswerStructure
from .code_response_engine import CodeResponseEngine
from .explanation_engine import ExplanationEngine
from .fact_checker import FactChecker
from .response_strategy import ResponseStrategy


class ResponseIntelligence:
    """
    Decide response type then structure / improve the answer.

    short | detailed | code | explanation | troubleshooting | comparison | step-by-step
    """

    def __init__(self) -> None:
        self.strategy = ResponseStrategy()
        self.structure = AnswerStructure()
        self.explanation = ExplanationEngine()
        self.code = CodeResponseEngine()
        self.facts = FactChecker()
        self.improve = AnswerImprovement()

    def run(
        self,
        message: str,
        answer: str = "",
        *,
        intent: str = "",
        strategy: str = "",
    ) -> dict[str, Any]:
        intent_key = (intent or "general").lower()
        strat = strategy or self.strategy.select(
            "implementation"
            if intent_key in {"coding", "code"}
            else (
                "explanation"
                if intent_key in {"explain", "explanation"}
                else ("planning" if intent_key in {"howto", "planning"} else "general")
            )
        )
        kind = self.structure.choose(strat, intent_key)
        draft = (answer or "").strip()

        if not draft and kind == "explanation":
            draft = self.explanation.explain(message).get("answer") or ""
        if kind == "code":
            draft = self.code.format(draft, message=message).get("answer") or draft

        structured = self.structure.apply(draft, kind=kind)
        check = self.facts.check(structured["answer"], message=message)
        improved = self.improve.improve(
            structured["answer"],
            message=message,
            structure_kind=kind,
            issues=list(check.get("flags") or []),
        )
        final = improved["answer"]
        return {
            "answer": final,
            "strategy": strat,
            "kind": kind,
            "sections": structured.get("sections") or [],
            "fact_check": check,
            "improved": bool(improved.get("changed")),
            "meta": {"step": 27, "flow": "strategy→structure→improve"},
        }


def run_response_intelligence(
    message: str,
    answer: str = "",
    *,
    intent: str = "",
    strategy: str = "",
) -> dict[str, Any]:
    return ResponseIntelligence().run(
        message, answer, intent=intent, strategy=strategy
    )
