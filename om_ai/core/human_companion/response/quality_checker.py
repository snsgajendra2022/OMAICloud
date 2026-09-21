"""Quality checker for companion replies."""
from __future__ import annotations

import re
from typing import Any


class QualityChecker:
    _BAD = re.compile(
        r"(?i)(how can i help you|as an ai|agent\s*\[|collaboration\s*:|retrieve context|"
        r"share one more detail|i can help with that|goal,\s*error,\s*or constraint)"
    )

    def check(self, answer: str, *, user_message: str = "", policy: dict[str, Any] | None = None) -> dict[str, Any]:
        text = (answer or "").strip()
        issues: list[str] = []
        if not text:
            issues.append("empty")
        if self._BAD.search(text):
            issues.append("banned_or_internal")
        if re.search(r"(?i)share one more detail|i can help with that|goal,\s*error", text):
            issues.append("robotic_filler")
        max_s = int((policy or {}).get("max_sentences") or 4)
        sentences = [s for s in re.split(r"(?<=[.!?।])\s+", text) if s.strip()]
        if len(sentences) > max_s + 2:
            issues.append("too_long")
        if len(text.split()) > 90:
            issues.append("wordy")
        return {
            "ok": not issues,
            "needs_improve": bool(issues),
            "issues": issues,
            "sentence_count": len(sentences),
        }
