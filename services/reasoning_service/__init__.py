"""Reasoning microservice."""
from __future__ import annotations

from typing import Any

from services._common import ServiceHealth, ok


class ReasoningService:
    def health(self) -> dict[str, Any]:
        return ServiceHealth("reasoning-service").to_dict()

    def analyze(self, question: str) -> dict[str, Any]:
        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

        return ok(run_reasoning_pipeline(question, retrieve=True))
