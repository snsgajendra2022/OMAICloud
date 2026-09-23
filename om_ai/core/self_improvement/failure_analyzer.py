"""Failure analyzer — what went wrong in a reply."""
from __future__ import annotations

from typing import Any


class FailureAnalyzer:
    def analyze(self, user: str, answer: str) -> dict[str, Any]:
        low = (answer or "").lower()
        issues = []
        if "how can i help you" in low:
            issues.append("helpdesk_phrase")
        if "as an ai" in low:
            issues.append("ai_disclaimer")
        if low.startswith("solve:") or "1. understand" in low:
            issues.append("solution_stub")
        if "explain your problem" in low or "please explain" in low:
            issues.append("robotic_interrogation")
        return {
            "failed": bool(issues),
            "issues": issues,
            "user_preview": (user or "")[:120],
        }
