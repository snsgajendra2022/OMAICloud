"""Evaluation microservice."""
from __future__ import annotations

from typing import Any

from services._common import ServiceHealth, ok


class EvaluationService:
    def health(self) -> dict[str, Any]:
        return ServiceHealth("evaluation-service").to_dict()

    def run(self, out: str = "artifacts/eval/platform_eval.json") -> dict[str, Any]:
        from om_ai.evaluation import run_evaluation

        return ok(run_evaluation(out=out, feed_learning=True))
