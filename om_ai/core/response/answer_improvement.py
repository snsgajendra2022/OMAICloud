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

        # Never inject chatbot filler — leave empty for companion rescue
        if not text:
            return {"answer": "", "changed": False, "issues": issues + ["empty"]}

        # Strip known robotic repair phrases if somehow present
        if re.search(
            r"(?i)share one more detail|goal,\s*error,\s*or constraint|i can help with that",
            text,
        ):
            return {
                "answer": "",
                "changed": True,
                "issues": issues + ["robotic_filler_removed"],
            }

        if "echo" in issues and message:
            text = (
                f"On “{message[:120].strip()}” — tell me the exact error or goal, "
                "and I’ll give you a direct next step."
            )
            changed = True

        if structure_kind == "troubleshooting" and "check" not in text.lower() and len(text) > 40:
            text = text + "\n\nIf this still fails, paste the exact error text for a precise fix."
            changed = True

        return {"answer": text, "changed": changed, "issues": issues}
