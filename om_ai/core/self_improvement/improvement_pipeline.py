"""
Conversation → Feedback → Failure → Learning Event → Dataset → Evaluation → Future Improvement

Never trains during live conversation.
"""
from __future__ import annotations

from typing import Any

from .evaluation_memory import EvaluationMemory
from .feedback_engine import FeedbackEngine
from .improvement_engine import ImprovementEngine

_PIPE: "ImprovementPipeline | None" = None


class ImprovementPipeline:
    def __init__(self) -> None:
        self.feedback = FeedbackEngine()
        self.engine = ImprovementEngine()
        self.evaluation = EvaluationMemory()
        # Keep legacy runtime if present
        try:
            from .learning_trigger import get_self_improvement

            self._legacy = get_self_improvement()
        except Exception:
            self._legacy = None

    def after_turn(
        self,
        *,
        user_message: str,
        answer: str,
        rating: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        fb = self.feedback.record(
            user_message=user_message, answer=answer, rating=rating, note=note
        )
        obs = self.engine.observe(user_message=user_message, answer=answer, feedback=fb)
        # Soft quality score
        score = 0.8
        if rating == "bad" or obs["event"].get("gaps"):
            score = 0.35
        elif rating == "good":
            score = 0.95
        self.evaluation.store(metric="turn_quality", value=score, note=note)
        return {
            "step": 68,
            "feedback": fb,
            "observation": obs,
            "evaluation": self.evaluation.summary(),
            "dataset_hint": "Append bad turns to offline SFT/DPO JSONL — never train live.",
        }


def get_improvement_pipeline() -> ImprovementPipeline:
    global _PIPE
    if _PIPE is None:
        _PIPE = ImprovementPipeline()
    return _PIPE
