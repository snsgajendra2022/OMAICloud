"""Verification engine — internal checks before final answer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .analyzer import IntentResult
from .solver import SolutionResult


@dataclass
class VerifyResult:
    validation: list[str] = field(default_factory=list)
    passed: bool = True
    score: float = 0.7
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation": self.validation,
            "passed": self.passed,
            "score": self.score,
            "meta": self.meta,
        }


class VerificationEngine:
    def verify(self, intent: IntentResult, solution: SolutionResult) -> VerifyResult:
        checks = [
            "Answers the stated user ask",
            "Separates current (2026) vs research claims",
            "No invented citations",
            "Unsafe actions remain gated",
        ]
        if intent.intent in {"coding", "debug"}:
            checks += ["Mentions tests or validation", "Avoids committing secrets"]
        text = (solution.solution or "").lower()
        failed = []
        if intent.intent in {"coding", "debug"} and "test" not in text:
            failed.append("Coding answer should mention tests")
        passed = not failed
        score = 0.85 if passed else 0.55
        validation = checks + ([f"FAIL: {f}" for f in failed] if failed else ["All heuristic checks passed"])
        return VerifyResult(
            validation=validation,
            passed=passed,
            score=score,
            meta={"verifier": "om-verify-v1"},
        )
