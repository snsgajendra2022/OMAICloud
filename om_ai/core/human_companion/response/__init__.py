"""Response intelligence — understand → reason → check → improve → answer."""
from __future__ import annotations

import re
from typing import Any, Callable

from .answer_strategy import AnswerStrategy
from .quality_checker import QualityChecker
from .response_planner import ResponsePlanner
from .self_evaluator import SelfEvaluator


class ResponseIntelligence:
    def __init__(self) -> None:
        self.planner = ResponsePlanner()
        self.strategy = AnswerStrategy()
        self.quality = QualityChecker()
        self.evaluator = SelfEvaluator()

    def run(
        self,
        message: str,
        *,
        generate: Callable[..., str] | None,
        context_blob: str = "",
        history: list[dict[str, Any]] | None = None,
        policy: dict[str, Any] | None = None,
        personality_hint: str = "",
        pre_answer: str = "",
    ) -> dict[str, Any]:
        plan = self.planner.plan(message, policy=policy)
        strat = self.strategy.select(plan, policy=policy)
        merged = "\n".join(
            p for p in (personality_hint, context_blob, strat.get("instruction", "")) if p
        ).strip()[:4000]

        answer = (pre_answer or "").strip()
        if not answer and generate:
            try:
                answer = str(generate(message, merged) or "").strip()
            except TypeError:
                try:
                    answer = str(generate(message) or "").strip()
                except Exception:
                    answer = ""
            except Exception:
                answer = ""

        check = self.quality.check(answer, user_message=message, policy=policy)
        if check.get("needs_improve") and generate:
            improve_prompt = (
                f"{message}\n\nRewrite this reply to be more natural, shorter, and companion-like. "
                f"Remove chatbot phrases. Original: {answer[:500]}"
            )
            try:
                improved = str(generate(improve_prompt, merged) or "").strip()
                if improved and len(improved) > 8:
                    answer = improved
                    check = self.quality.check(answer, user_message=message, policy=policy)
            except Exception:
                pass

        eval_pack = self.evaluator.score(answer, user_message=message)
        # Hard strip leftover banned lines
        answer = re.sub(
            r"(?i)\bhow can i help you\b[.!]?",
            "",
            answer or "",
        ).strip()
        return {
            "answer": answer,
            "plan": plan,
            "strategy": strat,
            "quality": check,
            "evaluation": eval_pack,
            "context_used": bool(merged),
        }
