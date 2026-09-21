"""Verification engine — check whether a drafted solution is sound."""
from __future__ import annotations

import re
from typing import Any


class VerificationEngine:
    """Score and gate solutions before they reach the user."""

    WEAK = (
        "as an ai",
        "i don't know how to",
        "could not produce",
        "couldn't produce",
        "how can i help you",
    )

    def verify(
        self,
        answer: str,
        *,
        message: str = "",
        analysis: dict[str, Any] | None = None,
        reasoning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        analysis = dict(analysis or {})
        reasoning = dict(reasoning or {})
        text = (answer or "").strip()
        low = text.lower()
        issues: list[str] = []

        if not text:
            issues.append("empty_answer")
        if len(text) < 24:
            issues.append("too_short")
        if any(w in low for w in self.WEAK):
            issues.append("weak_phrase")
        if analysis.get("problem_type") == "debugging":
            if not reasoning.get("checks") and "check" not in low:
                issues.append("missing_checks")
            if not reasoning.get("fix_order") and "fix" not in low and "1." not in text:
                issues.append("missing_fix_plan")
        if analysis.get("missing_information") and "?" not in text:
            # Soft issue — may still be ok if we proceeded
            issues.append("no_clarifying_question")

        score = 0.9
        score -= 0.15 * len([i for i in issues if i != "no_clarifying_question"])
        if "no_clarifying_question" in issues:
            score -= 0.05
        score = max(0.05, min(0.99, score))

        ok = score >= 0.55 and "empty_answer" not in issues and "weak_phrase" not in issues
        return {
            "ok": ok,
            "score": round(score, 3),
            "issues": issues,
            "needs_correction": (not ok) or ("empty_answer" in issues) or ("too_short" in issues),
            "verified": ok,
        }
