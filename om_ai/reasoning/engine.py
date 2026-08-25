"""Advanced reasoning architecture for OM (software layer).

Delegates to the foundation pipeline for rich domain solutions while keeping
ReasoningTrace for CLI / agents / eval harnesses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from om_ai.core.reasoning.pipeline import run_reasoning_pipeline


@dataclass
class ReasoningTrace:
    question: str
    decomposition: list[str] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    solution: str = ""
    critique: list[str] = field(default_factory=list)
    confidence: float = 0.5
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "decomposition": self.decomposition,
            "plan": self.plan,
            "verification": self.verification,
            "solution": self.solution,
            "critique": self.critique,
            "confidence": self.confidence,
            "meta": self.meta,
        }

    def as_markdown(self) -> str:
        md = (self.meta or {}).get("markdown")
        if md:
            return str(md)
        lines = [
            "## Understanding",
            self.question.strip(),
            "",
            "## Decomposition",
            *[f"- {x}" for x in self.decomposition],
            "",
            "## Plan",
            *[f"{i+1}. {x}" for i, x in enumerate(self.plan)],
            "",
            "## Verification",
            *[f"- {x}" for x in self.verification],
            "",
            "## Solution",
            self.solution,
            "",
            "## Self-critique",
            *[f"- {x}" for x in self.critique],
            "",
            f"_Confidence: {self.confidence:.2f}_",
        ]
        return "\n".join(lines)


class ReasoningEngine:
    """Structured reasoning via foundation pipeline (v2)."""

    def reason(self, question: str) -> ReasoningTrace:
        q = (question or "").strip() or "Empty question"
        result = run_reasoning_pipeline(q, retrieve=True)
        intent = result.get("intent") or {}
        conf = float(result.get("score") or 0.55)
        return ReasoningTrace(
            question=q,
            decomposition=[
                intent.get("understanding") or q,
                f"Intent: {intent.get('intent', 'general')}",
                f"Domain: {intent.get('domain', 'general')}",
            ],
            plan=list(result.get("plan") or []),
            verification=list(result.get("validation") or []),
            solution=str(result.get("solution") or ""),
            critique=list(result.get("critique") or []),
            confidence=conf,
            meta={
                "domain": intent.get("domain"),
                "engine": "om-reasoning-v2",
                "markdown": result.get("markdown"),
                "pipeline": result.get("meta"),
            },
        )


def reason(question: str) -> ReasoningTrace:
    return ReasoningEngine().reason(question)
