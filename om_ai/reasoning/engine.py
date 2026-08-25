"""Advanced reasoning architecture for OM (software layer).

Flow:
  Question → Decompose → Plan → Internal checks → Solution outline → Self-critique

This does **not** replace a large trained model; it structures thinking for
agents, SFT targets, and eval harnesses.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


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
    """Rule + heuristic chain / reflection (LLM can refine later)."""

    CODING_HINTS = re.compile(
        r"\b(code|api|fastapi|react|bug|refactor|deploy|test|repo|function|class)\b",
        re.I,
    )
    MATH_HINTS = re.compile(r"\b(prove|integral|equation|probability|matrix|derive)\b", re.I)
    RESEARCH_HINTS = re.compile(r"\b(research|paper|survey|compare|history|1600|physics)\b", re.I)

    def reason(self, question: str) -> ReasoningTrace:
        q = (question or "").strip() or "Empty question"
        domain = self._domain(q)
        parts = self._decompose(q, domain)
        plan = self._plan(q, domain, parts)
        checks = self._verify(q, domain, plan)
        solution = self._solution(q, domain, parts, plan)
        critique = self._critique(q, domain, solution, checks)
        conf = 0.55
        if domain == "coding":
            conf = 0.6
        if len(q) < 20:
            conf = 0.4
        if any("unknown" in c.lower() or "need data" in c.lower() for c in critique):
            conf = min(conf, 0.45)
        return ReasoningTrace(
            question=q,
            decomposition=parts,
            plan=plan,
            verification=checks,
            solution=solution,
            critique=critique,
            confidence=conf,
            meta={"domain": domain, "engine": "om-reasoning-v1"},
        )

    def _domain(self, q: str) -> str:
        if self.CODING_HINTS.search(q):
            return "coding"
        if self.MATH_HINTS.search(q):
            return "math"
        if self.RESEARCH_HINTS.search(q):
            return "research"
        return "general"

    def _decompose(self, q: str, domain: str) -> list[str]:
        base = [
            "Clarify the user goal and success criteria",
            "List constraints (time, safety, stack, data)",
            "Identify required knowledge domains",
        ]
        if domain == "coding":
            base += [
                "Locate relevant modules / APIs",
                "Define interfaces and failure modes",
                "Specify tests that prove the fix",
            ]
        elif domain == "math":
            base += ["State knowns/unknowns", "Choose method", "Check edge cases"]
        elif domain == "research":
            base += [
                "Separate 2026-current vs research horizons",
                "List sources to retrieve (RAG / docs)",
            ]
        else:
            base += ["Break into 2–5 sub-questions", "Order by dependency"]
        # light split on conjunctions
        chunks = [c.strip() for c in re.split(r"[?;]|\\band then\\b|\\bthen\\b", q) if c.strip()]
        if len(chunks) > 1:
            base.append("Sub-questions: " + " | ".join(chunks[:5]))
        return base

    def _plan(self, q: str, domain: str, parts: list[str]) -> list[str]:
        plan = [
            "Gather context (memory / RAG / repo map)",
            "Draft approach using first principles",
            "Select tools or agents",
            "Execute smallest safe step",
            "Validate against success criteria",
        ]
        if domain == "coding":
            plan = [
                "Map repository / entrypoints",
                "Write failing test or reproduction",
                "Implement minimal change",
                "Run tests / typecheck",
                "Review security and edge cases",
                "Document next steps",
            ]
        return plan

    def _verify(self, q: str, domain: str, plan: list[str]) -> list[str]:
        checks = [
            "Does the plan answer the asked question (not a related one)?",
            "Are research claims labeled vs production-ready (2026)?",
            "Any unsafe shell / hardware actions gated?",
        ]
        if domain == "coding":
            checks += [
                "Is there a test that would fail before the fix?",
                "Are secrets excluded from diffs?",
            ]
        return checks

    def _solution(
        self, q: str, domain: str, parts: list[str], plan: list[str]
    ) -> str:
        return (
            f"**Domain:** {domain}\n\n"
            f"**Approach:** Execute the plan in order, using OM Knowledge Brain + agents "
            f"when needed. Prefer architecture → implementation → validation.\n\n"
            f"**Immediate next action:** {plan[0] if plan else 'Clarify requirements.'}\n\n"
            f"**User ask:** {q}"
        )

    def _critique(
        self, q: str, domain: str, solution: str, checks: list[str]
    ) -> list[str]:
        out = [
            "Heuristic engine only — large OM weights improve answer quality.",
            "If facts are required, retrieve from Knowledge Universe / RAG before asserting.",
        ]
        if domain == "general" and len(q) > 120:
            out.append("Long general ask — consider splitting into parallel agent tasks.")
        if "deploy" in q.lower():
            out.append("Deployment needs environment secrets and rollback plan — need data.")
        return out


def reason(question: str) -> ReasoningTrace:
    return ReasoningEngine().reason(question)
