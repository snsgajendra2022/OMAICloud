"""Reproducible evaluation primitives for candidate OM model responses."""
from __future__ import annotations

from typing import Any, Callable


class EvaluationEngine:
    """Evaluate an injected generator against held-out examples.

    This is a smoke/regression harness, not a claim of human-level factuality
    measurement. Production promotion should also use task-specific benchmarks
    and human review.
    """

    def evaluate(
        self,
        examples: list[dict[str, Any]],
        generate: Callable[[str], str],
    ) -> dict[str, Any]:
        total = len(examples)
        if total == 0:
            return {
                "passed": False,
                "count": 0,
                "non_empty_rate": 0.0,
                "echo_rate": 0.0,
                "errors": ["Evaluation set is empty."],
            }
        non_empty = 0
        echoes = 0
        errors: list[dict[str, str]] = []
        for index, row in enumerate(examples):
            question = str(row.get("question") or "").strip()
            if not question:
                errors.append({"index": str(index), "error": "missing_question"})
                continue
            try:
                answer = str(generate(question) or "").strip()
            except Exception as exc:
                errors.append({"index": str(index), "error": type(exc).__name__})
                continue
            if answer:
                non_empty += 1
            if self._normalize(answer) == self._normalize(question):
                echoes += 1
        non_empty_rate = non_empty / total
        echo_rate = echoes / total
        return {
            "passed": not errors and non_empty_rate >= 0.95 and echo_rate <= 0.01,
            "count": total,
            "non_empty_rate": round(non_empty_rate, 4),
            "echo_rate": round(echo_rate, 4),
            "errors": errors[:100],
        }

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())
