"""Solution engine — GPT-style problem-solving orchestrator for chat intelligence.

Pipeline:
  problem → memory → hypotheses → plan → reason → explain → verify → correct → confidence → remember
"""
from __future__ import annotations

import re
import time
import uuid
from typing import Any, Callable

from .confidence_engine import ConfidenceEngine
from .correction_engine import CorrectionEngine
from .explanation_engine import ExplanationEngine
from .hypothesis_engine import HypothesisEngine
from .problem_analyzer import ProblemAnalyzer
from .reasoning_engine import ReasoningEngine
from .solution_memory import SolutionMemory
from .solution_planner import SolutionPlanner
from .verification_engine import VerificationEngine


class SolutionEngine:
    """Production orchestrator — connects all solution intelligence components."""

    def __init__(
        self,
        *,
        problem_analyzer: ProblemAnalyzer | None = None,
        hypothesis_engine: HypothesisEngine | None = None,
        solution_planner: SolutionPlanner | None = None,
        reasoning_engine: ReasoningEngine | None = None,
        explanation_engine: ExplanationEngine | None = None,
        verification_engine: VerificationEngine | None = None,
        confidence_engine: ConfidenceEngine | None = None,
        correction_engine: CorrectionEngine | None = None,
        solution_memory: SolutionMemory | None = None,
    ) -> None:
        self.problem_analyzer = problem_analyzer or ProblemAnalyzer()
        self.hypothesis_engine = hypothesis_engine or HypothesisEngine()
        self.solution_planner = solution_planner or SolutionPlanner()
        self.reasoning_engine = reasoning_engine or ReasoningEngine()
        self.explanation_engine = explanation_engine or ExplanationEngine()
        self.verification_engine = verification_engine or VerificationEngine()
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.correction_engine = correction_engine or CorrectionEngine()
        self.solution_memory = solution_memory or SolutionMemory()

    def solve(
        self,
        message: str,
        *,
        plan: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        model_generate: Callable[..., str] | None = None,
        knowledge: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        start = time.time()
        plan = dict(plan or {})
        context = dict(context or {})
        knowledge = dict(knowledge or {})
        q = (message or "").strip()

        if self._is_personal(q):
            return {
                "id": request_id,
                "solved": False,
                "answer": "",
                "kind": "none",
                "notes": ["personal"],
                "complete": False,
            }

        analysis = self.problem_analyzer.analyze(q, context=context, plan=plan)
        memory_hits = self.solution_memory.recall(q, analysis=analysis)
        hypotheses = self.hypothesis_engine.generate(
            q, analysis=analysis, memory_hits=memory_hits
        )
        sol_plan = self.solution_planner.plan(
            analysis=analysis,
            hypotheses=hypotheses,
            answer_plan=plan,
        )
        reasoning = self.reasoning_engine.reason(
            q,
            analysis=analysis,
            hypotheses=hypotheses,
            plan=sol_plan,
            knowledge=knowledge,
            model_generate=model_generate,
        )
        explained = self.explanation_engine.explain(
            q,
            analysis=analysis,
            reasoning=reasoning,
            plan=sol_plan,
            model_generate=model_generate,
        )
        answer = str(explained.get("answer") or "").strip()
        verification = self.verification_engine.verify(
            answer, message=q, analysis=analysis, reasoning=reasoning
        )

        corrected = False
        if verification.get("needs_correction"):
            retry = self.explanation_engine.explain(
                q,
                analysis=analysis,
                reasoning=reasoning,
                plan={**sol_plan, "ask_details": False},
                model_generate=model_generate,
            )
            pack = self.correction_engine.correct(
                q,
                answer,
                solution={"answer": retry.get("answer") or answer, "solved": True},
                intent=str(analysis.get("problem_type") or ""),
            )
            retry_ans = str(retry.get("answer") or "").strip()
            if pack.get("corrected") or (retry_ans and len(retry_ans) > len(answer)):
                answer = str(pack.get("answer") or retry_ans or answer).strip()
                corrected = True
                verification = self.verification_engine.verify(
                    answer, message=q, analysis=analysis, reasoning=reasoning
                )

        conf = self.confidence_engine.score(
            intent=str(analysis.get("problem_type") or ""),
            quality={
                "score": float(verification.get("score") or 0.5),
                "ok": verification.get("ok"),
            },
            solution={
                "solved": True,
                "complete": bool(explained.get("complete")),
            },
            used_model=bool(reasoning.get("model_trace")),
            corrected=corrected,
        )

        solved = bool(answer) and bool(verification.get("ok") or len(answer) >= 40)
        result = {
            "id": request_id,
            "solved": solved,
            "answer": answer,
            "kind": explained.get("kind") or analysis.get("problem_type") or "solution",
            "complete": bool(explained.get("complete")),
            "notes": [str((hypotheses.get("top") or {}).get("claim") or "")],
            "checks": list(reasoning.get("checks") or []),
            "analysis": analysis,
            "hypotheses": hypotheses,
            "plan": sol_plan,
            "reasoning": reasoning,
            "verification": verification,
            "confidence": conf.get("confidence"),
            "confidence_pack": conf,
            "corrected": corrected,
            "memory_hits": len(memory_hits),
            "execution_time": round(time.time() - start, 3),
        }

        if solved:
            self.solution_memory.store(
                message=q,
                analysis=analysis,
                solution=result,
                confidence=float(conf.get("confidence") or 0),
            )
        return result

    @staticmethod
    def _is_personal(q: str) -> bool:
        return bool(
            re.search(r"(?i)\b(my\s+name|mera\s+naam|who\s+am\s+i)\b", q or "")
        )
