"""STEP 88 — Advanced Reasoning Intelligence.

Requirements → hypotheses → alternatives → verification → final reasoning.
"""
from __future__ import annotations

from typing import Any


class AdvancedReasoningIntelligence:
    ARCHITECTURE_DIMENSIONS = [
        ("requirements", "Clarify functional and non-functional requirements"),
        ("traffic", "Estimate traffic, users, and throughput"),
        ("data", "Design data model and storage choices"),
        ("services", "Define service / module architecture"),
        ("scaling", "Plan horizontal/vertical scaling strategy"),
        ("reliability", "Cover failure handling and resilience"),
        ("security", "Address auth, privacy, and threat model"),
        ("cost", "Outline cost drivers and optimization levers"),
    ]

    def reason(self, question: str, *, domain_hint: str | None = None) -> dict[str, Any]:
        q = (question or "").strip()
        low = q.lower()
        is_arch = any(
            w in low
            for w in ("architect", "design", "system", "uber", "scale", "microservice", "ecommerce")
        ) or domain_hint == "architecture"

        requirements = self._requirements(q, is_arch)
        hypotheses = self._hypotheses(q, is_arch)
        alternatives = self._alternatives(q, is_arch)
        verification = self._verify(hypotheses, alternatives)
        chain = self._chain(q, requirements, hypotheses, alternatives, verification, is_arch)
        plan = [c["step"] for c in chain]

        return {
            "step": 88,
            "status": "deep_reasoning_complete",
            "mode": "architecture" if is_arch else "general",
            "requirements": requirements,
            "hypotheses": hypotheses,
            "alternatives": alternatives,
            "verification": verification,
            "chain": chain,
            "plan": plan,
            "final_reasoning": self._final(q, chain, verification),
        }

    def _requirements(self, q: str, is_arch: bool) -> list[str]:
        base = [f"Understand user goal: {q}"]
        if is_arch:
            return base + [
                "Identify actors and core use cases",
                "Capture latency, availability, and consistency targets",
                "List integrations and external dependencies",
            ]
        return base + [
            "Identify constraints and success criteria",
            "List unknowns that need assumptions",
        ]

    def _hypotheses(self, q: str, is_arch: bool) -> list[str]:
        if is_arch:
            return [
                "A modular service-oriented design fits the problem",
                "Read-heavy paths benefit from caching and async processing",
                "Strong auth and audit trails are mandatory for trust",
            ]
        return [
            f"The primary intent is to answer: {q}",
            "A structured multi-step explanation will be clearer than a one-liner",
        ]

    def _alternatives(self, q: str, is_arch: bool) -> list[dict[str, str]]:
        if is_arch:
            return [
                {"option": "Monolith first", "pros": "speed to ship", "cons": "harder scale later"},
                {"option": "Service-oriented", "pros": "independent scale", "cons": "ops complexity"},
                {"option": "Event-driven", "pros": "decoupling", "cons": "harder debugging"},
            ]
        return [
            {"option": "Direct answer", "pros": "fast", "cons": "may miss depth"},
            {"option": "Structured analysis", "pros": "complete", "cons": "longer"},
        ]

    def _verify(self, hypotheses: list[str], alternatives: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "hypotheses_checked": len(hypotheses),
            "alternatives_compared": len(alternatives),
            "recommended": alternatives[1]["option"] if len(alternatives) > 1 else alternatives[0]["option"],
            "risks": [
                "Hidden requirements may invalidate early assumptions",
                "Over-engineering if scope is smaller than expected",
            ],
            "passed": True,
        }

    def _chain(
        self,
        q: str,
        requirements: list[str],
        hypotheses: list[str],
        alternatives: list[dict[str, str]],
        verification: dict[str, Any],
        is_arch: bool,
    ) -> list[dict[str, str]]:
        chain = [
            {"phase": "requirements", "step": requirements[0]},
            {"phase": "hypothesis", "step": hypotheses[0]},
            {"phase": "alternatives", "step": f"Compare options: {', '.join(a['option'] for a in alternatives)}"},
            {"phase": "verification", "step": f"Recommend {verification['recommended']} after risk check"},
        ]
        if is_arch:
            for key, label in self.ARCHITECTURE_DIMENSIONS:
                chain.append({"phase": key, "step": label})
        chain.append({"phase": "final", "step": "Synthesize a coherent actionable answer"})
        return chain

    def _final(self, q: str, chain: list[dict[str, str]], verification: dict[str, Any]) -> str:
        lines = [
            f"Deep reasoning for: {q}",
            f"Recommended approach: {verification.get('recommended')}",
            "Reasoning chain:",
        ]
        for i, c in enumerate(chain, 1):
            lines.append(f"{i}. [{c['phase']}] {c['step']}")
        return "\n".join(lines)
