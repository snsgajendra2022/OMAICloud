"""STEP 29 — Continuous conversation learning manager."""
from __future__ import annotations

from typing import Any

from .feedback_collector import FeedbackCollector
from .failure_analyzer import FailureAnalyzer
from .improvement_loop import ImprovementLoop
from .knowledge_gap import KnowledgeGapRegistry
from .learning_scheduler import LearningScheduler


class LearningManager:
    def __init__(self) -> None:
        self.feedback = FeedbackCollector()
        self.failures = FailureAnalyzer()
        self.gaps = KnowledgeGapRegistry()
        self.loop = ImprovementLoop()
        self.scheduler = LearningScheduler()

    def observe(
        self,
        message: str,
        answer: str,
        *,
        quality: dict[str, Any] | None = None,
        rating: float | None = None,
    ) -> dict[str, Any]:
        analysis = self.failures.analyze(message, answer, quality=quality)
        rating_v = float(rating if rating is not None else (0.3 if analysis["failed"] else 0.8))
        fb = self.feedback.add(
            message,
            answer,
            rating=rating_v,
            reason=",".join(analysis.get("issues") or []),
        )
        if analysis.get("failed") and analysis.get("gap"):
            self.gaps.record(str(analysis["gap"]), example=message)
        return {"feedback": fb, "analysis": analysis, "gaps": self.gaps.snapshot()}

    def improve(self) -> dict[str, Any]:
        negs = self.feedback.negatives()
        gap_list = self.gaps.top()
        loop = self.loop.run(
            failures=[
                {
                    "message": n.get("message"),
                    "issues": (n.get("reason") or "").split(","),
                    "gap": "coding" if "code" in (n.get("message") or "").lower() else "conversation",
                }
                for n in negs
            ],
            gaps=gap_list,
        )
        schedule = self.scheduler.schedule(gap_list)
        return {"step": 29, "loop": loop, "schedule": schedule, "gaps": gap_list}


def run_continuous_learning(
    message: str = "",
    answer: str = "",
    *,
    quality: dict[str, Any] | None = None,
    improve: bool = False,
) -> dict[str, Any]:
    mgr = LearningManager()
    observed = {}
    if message or answer:
        observed = mgr.observe(message, answer, quality=quality)
    out = {"observed": observed}
    if improve or observed.get("analysis", {}).get("failed"):
        out["improve"] = mgr.improve()
    out["step"] = 29
    return out
