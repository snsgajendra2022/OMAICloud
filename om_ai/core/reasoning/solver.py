"""Solution generator (structured outline; LLM can refine later)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .analyzer import IntentResult
from .planner import PlanResult


@dataclass
class SolutionResult:
    solution: str
    architecture: list[str] = field(default_factory=list)
    implementation_notes: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "solution": self.solution,
            "architecture": self.architecture,
            "implementation_notes": self.implementation_notes,
            "meta": self.meta,
        }


class SolutionGenerator:
    def solve(
        self,
        question: str,
        intent: IntentResult,
        plan: PlanResult,
        *,
        knowledge_hits: list[str] | None = None,
    ) -> SolutionResult:
        hits = knowledge_hits or []
        arch = [
            "Understanding layer",
            "Knowledge retrieval",
            "Planning + agent selection",
            "Implementation",
            "Verification",
        ]
        notes = [
            f"Intent={intent.intent} domain={intent.domain}",
            f"Agents: {', '.join(plan.agents)}",
            "Prefer 2026-current facts; label research horizons",
        ]
        if hits:
            notes.append(f"Retrieved {len(hits)} knowledge snippets")
        solution = (
            f"**Understanding:** {intent.understanding}\n\n"
            f"**Plan:**\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan.plan)) + "\n\n"
            f"**Approach:** Execute the plan with OM tools/agents. "
            f"Use Knowledge Universe when facts are required.\n\n"
            f"**Ask:** {question.strip()[:500]}"
        )
        if hits:
            solution += "\n\n**Knowledge context:**\n" + "\n".join(f"- {h[:200]}" for h in hits[:5])
        return SolutionResult(
            solution=solution,
            architecture=arch,
            implementation_notes=notes,
            meta={"solver": "om-solver-v1"},
        )
