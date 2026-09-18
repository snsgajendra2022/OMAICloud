"""STEP 28 — Native Model Improvement Layer."""
from __future__ import annotations

from typing import Any, Callable

from .checkpoint_selector import CheckpointSelector
from .curriculum_engine import CurriculumEngine
from .evaluation_engine import EvaluationEngine
from .model_benchmark import ModelBenchmark
from .training_scheduler import TrainingScheduler


class ModelImprovementLayer:
    def __init__(self) -> None:
        self.curriculum = CurriculumEngine()
        self.scheduler = TrainingScheduler()
        self.evaluation = EvaluationEngine()
        self.selector = CheckpointSelector()
        self.benchmark = ModelBenchmark()

    def run(
        self,
        *,
        gaps: list[str] | None = None,
        generate: Callable[[str], str] | None = None,
        candidates: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        curr = self.curriculum.build(gaps)
        plan = self.scheduler.plan(curr)
        bench = self.benchmark.run(generate)
        eval_pack = self.evaluation.evaluate(
            {r["track"]: (1.0 if r["ok"] else 0.4) for r in bench.get("results") or []}
        )
        chosen = self.selector.select(
            candidates
            or [
                {"name": "om-1.0-current", "score": eval_pack["overall"]},
                {"name": "om-1.0-candidate", "score": max(0.0, eval_pack["overall"] - 0.05)},
            ]
        )
        return {
            "step": 28,
            "curriculum": curr,
            "training_plan": plan,
            "benchmark": bench,
            "evaluation": eval_pack,
            "checkpoint": chosen,
            "flow": "data→train→eval→checkpoint→deploy",
        }


def run_model_improvement(**kwargs: Any) -> dict[str, Any]:
    return ModelImprovementLayer().run(**kwargs)
