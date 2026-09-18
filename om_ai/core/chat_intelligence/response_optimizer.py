"""Response optimizer — clarity / completeness checks."""
from __future__ import annotations

import re
from typing import Any


class ResponseOptimizer:
    """Improve answer clarity and completeness before send."""

    GIBBERISH = re.compile(r"(.)\1{8,}")
    PIPELINE_LEAK = re.compile(
        r"\b(trace_id|internal_context|stage[s]?:|OM_CHAT_|tokenizer)\b",
        re.I,
    )

    def evaluate(self, answer: str, *, message: str = "", intent: str = "") -> dict[str, Any]:
        text = (answer or "").strip()
        issues: list[str] = []
        score = 1.0

        if not text:
            issues.append("empty")
            score = 0.0
        elif len(text) < 12 and intent not in {"thanks", "goodbye", "greeting", "morning", "evening", "afternoon"}:
            issues.append("too_short")
            score -= 0.35
        if self.GIBBERISH.search(text):
            issues.append("gibberish")
            score -= 0.5
        if self.PIPELINE_LEAK.search(text):
            issues.append("pipeline_leak")
            score -= 0.6
        if message and text.lower().strip() == message.lower().strip():
            issues.append("echo")
            score -= 0.5
        if intent == "debugging" and "check" not in text.lower() and "fix" not in text.lower():
            issues.append("missing_debug_structure")
            score -= 0.2

        score = max(0.0, min(1.0, score))
        return {
            "ok": score >= 0.55 and "empty" not in issues and "gibberish" not in issues,
            "score": score,
            "issues": issues,
            "complete": "too_short" not in issues and "empty" not in issues,
            "clear": "gibberish" not in issues and "pipeline_leak" not in issues,
        }

    def optimize(
        self,
        answer: str,
        *,
        message: str = "",
        intent: str = "",
        fallback: str = "",
    ) -> dict[str, Any]:
        text = (answer or "").strip()
        report = self.evaluate(text, message=message, intent=intent)
        improved = text

        # Light cleanup
        improved = re.sub(r"\n{3,}", "\n\n", improved).strip()
        if report["issues"]:
            if "pipeline_leak" in report["issues"] or "gibberish" in report["issues"]:
                improved = (fallback or "").strip() or improved
            if "empty" in report["issues"] or "echo" in report["issues"]:
                improved = (fallback or "").strip() or (
                    "I want to help — could you rephrase that in one short sentence?"
                )

        final_report = self.evaluate(improved, message=message, intent=intent)
        return {
            "answer": improved,
            "report": final_report,
            "changed": improved != text,
        }
