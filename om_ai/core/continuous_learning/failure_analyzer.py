"""STEP 29 — Failure analyzer."""
from __future__ import annotations

from typing import Any


class FailureAnalyzer:
    def analyze(self, message: str, answer: str, *, quality: dict[str, Any] | None = None) -> dict[str, Any]:
        quality = dict(quality or {})
        text = (answer or "").strip()
        issues: list[str] = []
        if not text:
            issues.append("empty_answer")
        if len(text) < 20:
            issues.append("too_short")
        if quality.get("ok") is False or float(quality.get("score") or 1) < 0.5:
            issues.append("low_quality")
        if "couldn't produce" in text.lower() or "clear answer" in text.lower():
            issues.append("fallback_phrase")
        gap = "conversation"
        low = (message or "").lower()
        if any(w in low for w in ("code", "react", "python", "bug", "error")):
            gap = "coding"
        elif any(w in low for w in ("why", "explain", "compare")):
            gap = "reasoning"
        return {
            "failed": bool(issues),
            "issues": issues,
            "gap": gap if issues else "",
            "severity": round(min(1.0, 0.3 * len(issues)), 2),
        }
