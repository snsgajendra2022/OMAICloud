"""Final response integrity gate for OM Chat Intelligence.

This gate checks basic usability and known defect signals. It does not claim
that an answer is factually correct; factual verification is a separate step.
"""
from __future__ import annotations

from typing import Any


class ChatQualityEngine:
    """Aggregate structural quality and verification metadata."""

    def evaluate(
        self,
        answer: str,
        *,
        optimizer_report: dict[str, Any] | None = None,
        confidence: dict[str, Any] | None = None,
        intent: str = "",
        verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = (answer or "").strip()
        optimizer_report = dict(optimizer_report or {})
        confidence = dict(confidence or {})
        verification = dict(verification or {})

        issues = list(dict.fromkeys(optimizer_report.get("issues") or []))
        try:
            score = float(optimizer_report.get("score") if optimizer_report.get("score") is not None else (0.75 if text else 0.0))
        except (TypeError, ValueError):
            score = 0.0
            issues.append("invalid_quality_score")
        try:
            conf = float(confidence.get("confidence") if confidence.get("confidence") is not None else 0.5)
        except (TypeError, ValueError):
            conf = 0.0
            issues.append("invalid_confidence_score")

        if not text:
            issues.append("empty")
            score = 0.0
        if not 0.0 <= score <= 1.0:
            issues.append("quality_score_out_of_range")
            score = min(1.0, max(0.0, score))
        if not 0.0 <= conf <= 1.0:
            issues.append("confidence_out_of_range")
            conf = min(1.0, max(0.0, conf))
        if conf < 0.4:
            issues.append("low_confidence")
        if verification.get("status") == "verification_failed":
            issues.append("independent_verification_failed")
        if verification.get("status") in (None, "", "unverified"):
            issues.append("factuality_not_independently_verified")

        # Keep legacy key for callers, but define it as a basic usability gate.
        approved = bool(text) and score >= 0.5 and not any(
            issue in issues for issue in (
                "gibberish", "empty", "independent_verification_failed",
            )
        )
        factuality_verified = verification.get("verified") is True
        return {
            "approved": approved,
            "basic_quality_passed": approved,
            "factuality_verified": factuality_verified,
            "status": "verified" if factuality_verified else ("verification_failed" if verification.get("status") == "verification_failed" else "unverified"),
            "score": round(score, 3),
            "confidence": round(conf, 3),
            "issues": list(dict.fromkeys(issues)),
            "intent": intent,
            "limitations": [
                "A quality score is not a probability that the answer is true.",
                "Approval means only that basic usability checks passed.",
            ],
        }

    def improve(
        self,
        answer: str,
        *,
        question: str = "",
        optimizer_report: dict[str, Any] | None = None,
        confidence: dict[str, Any] | None = None,
    ) -> str:
        """Perform conservative whitespace cleanup without inventing facts."""
        text = (answer or "").strip()
        if not text:
            return text
        report = self.evaluate(
            text,
            optimizer_report=optimizer_report,
            confidence=confidence,
            intent="",
        )
        if report.get("basic_quality_passed"):
            return text
        cleaned = " ".join(text.split())
        if question and cleaned.casefold() == question.strip().casefold():
            return text
        return cleaned or text
