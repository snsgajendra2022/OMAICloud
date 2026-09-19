from __future__ import annotations
from typing import Any

class ConversationAnalyzer:
    def analyze(self, user: str, answer: str) -> dict[str, Any]:
        issues = []
        a = (answer or "").lower()
        if not (answer or "").strip():
            issues.append("empty")
        if "rephrase" in a or "short sentence" in a:
            issues.append("robotic_fallback")
        if len((answer or "").split()) > 80:
            issues.append("too_long_for_voice")
        if "?" not in (answer or "") and len((user or "").split()) <= 6:
            issues.append("no_followup")
        return {"issues": issues, "ok": not issues}
