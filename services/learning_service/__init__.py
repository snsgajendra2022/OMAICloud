"""Learning / continuous improvement microservice."""
from __future__ import annotations

from typing import Any

from services._common import ServiceHealth, ok


class LearningService:
    def health(self) -> dict[str, Any]:
        return ServiceHealth("learning-service").to_dict()

    def improve(self, question: str, answer: str) -> dict[str, Any]:
        from om_ai.improvement import improve_from_exchange

        return ok(improve_from_exchange(question, answer))

    def export(self, out: str = "data/continuous") -> dict[str, Any]:
        from om_ai.learning import run_learning_cycle

        return ok(run_learning_cycle(out_dir=out))
