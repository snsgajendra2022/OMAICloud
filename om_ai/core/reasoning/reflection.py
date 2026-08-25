"""Self-reflection / critique for continuous improvement signals."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .verifier import VerifyResult


@dataclass
class ReflectionResult:
    critique: list[str] = field(default_factory=list)
    weak_areas: list[str] = field(default_factory=list)
    training_hints: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "critique": self.critique,
            "weak_areas": self.weak_areas,
            "training_hints": self.training_hints,
            "meta": self.meta,
        }


class ReflectionEngine:
    def reflect(self, verify: VerifyResult, *, domain: str = "general") -> ReflectionResult:
        critique = [
            "Heuristic foundation path — larger OM weights improve depth",
            "Retrieve licensed Knowledge Universe docs for factual density",
        ]
        weak: list[str] = []
        hints: list[str] = []
        if not verify.passed:
            weak.append(domain or "general")
            hints.append("Create SFT example covering the failed check")
        if verify.score < 0.7:
            weak.append("verification")
            hints.append("Add preference pair: weaker vs stronger structured answer")
        return ReflectionResult(
            critique=critique,
            weak_areas=weak,
            training_hints=hints,
            meta={"reflection": "om-reflect-v1"},
        )
