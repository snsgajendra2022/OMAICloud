"""STEP 27 — Answer improvement pass."""
from __future__ import annotations

import re
from typing import Any


class AnswerImprovement:
    def improve(
        self,
        answer: str,
        *,
        message: str = "",
        structure_kind: str = "detailed",
        issues: list[str] | None = None,
    ) -> dict[str, Any]:
        text = re.sub(r"\n{3,}", "\n\n", (answer or "").strip())
        changed = False
        issues = list(issues or [])

        if not text:
            text = (
                "I can help with that. "
                "Share one more detail (goal, error, or constraint) and I will give a concrete answer."
            )
            changed = True
            issues.append("empty_repaired")

        if "echo" in issues and message:
            text = (
                f"You asked about: {message[:180].strip()}\n\n"
                "Here is a clearer response: I can provide steps, an explanation, or code — "
                "tell me which you prefer."
            )
            changed = True

        if structure_kind == "troubleshooting" and "check" not in text.lower() and len(text) > 40:
            text = text + "\n\nIf this still fails, paste the exact error text for a precise fix."
            changed = True

        return {"answer": text, "changed": changed, "issues": issues}
