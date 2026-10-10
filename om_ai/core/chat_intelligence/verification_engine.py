"""Answer integrity checks for OM Chat Intelligence.

Structural checks can find obvious defects; they cannot prove factual truth.
The `verified` field is only true when an independent verification result is
explicitly supplied by a trusted caller.
"""
from __future__ import annotations

from typing import Any


class VerificationEngine:
    """Check answer structure and report verification status honestly."""

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
        independent_checks_passed: bool | None = None,
        verification_evidence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        analysis = dict(analysis or {})
        reasoning = dict(reasoning or {})
        evidence = [
            item for item in (verification_evidence or [])
            if isinstance(item, dict) and item.get("passed") is True
        ]
        text = (answer or "").strip()
        low = text.casefold()
        issues: list[str] = []

        if not text:
            issues.append("empty_answer")
        if len(text) < 24:
            issues.append("too_short")
        if any(phrase in low for phrase in self.WEAK):
            issues.append("weak_phrase")
        if message.strip() and text.casefold() == message.strip().casefold():
            issues.append("echoes_user_request")

        if analysis.get("problem_type") == "debugging":
            if not reasoning.get("checks") and "check" not in low and "test" not in low:
                issues.append("missing_checks")
            if not reasoning.get("fix_order") and "fix" not in low and "1." not in text:
                issues.append("missing_fix_plan")
        if analysis.get("missing_information") and "?" not in text:
            issues.append("no_clarifying_question")

        structural_issues = [
            issue for issue in issues
            if issue not in {"no_clarifying_question"}
        ]
        score = max(0.05, min(0.99, 1.0 - 0.15 * len(structural_issues)
                              - (0.05 if "no_clarifying_question" in issues else 0.0)))
        structurally_acceptable = bool(text) and score >= 0.55 and "weak_phrase" not in issues

        # Do not equate a heuristic score with factual verification.
        verified = independent_checks_passed is True
        if independent_checks_passed is False:
            issues.append("independent_verification_failed")
        elif independent_checks_passed is None:
            issues.append("independent_verification_not_run")

        return {
            "ok": structurally_acceptable,
            "score": round(score, 3),
            "issues": issues,
            "needs_correction": not structurally_acceptable or independent_checks_passed is False,
            "verified": verified,
            "status": (
                "verified" if verified else
                "verification_failed" if independent_checks_passed is False else
                "unverified"
            ),
            "verification_evidence": evidence,
            "verification_limitations": [
                "Structural checks are heuristic and do not establish factual truth.",
                "Only trusted independent checks should set independent_checks_passed=True.",
                "An empty evidence list does not prove that no verification occurred; record evidence when available.",
            ],
        }
