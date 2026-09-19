"""Correction engine — detect weak/wrong answers and upgrade them."""
from __future__ import annotations

import re
from typing import Any


class CorrectionEngine:
    """Second-pass correction when the model answer is weak."""

    FAILURE_PHRASES = (
        "couldn't produce a clear answer",
        "could not produce a clear answer",
        "i don't know how to",
        "as an ai language model",
        "i cannot help with that",
        "sorry, i can't assist",
    )

    def needs_correction(self, answer: str, *, quality_ok: bool = True) -> bool:
        text = (answer or "").strip().lower()
        if not text:
            return True
        if not quality_ok:
            return True
        if any(p in text for p in self.FAILURE_PHRASES):
            return True
        if len(text) < 8:
            return True
        if re.search(r"(.)\1{10,}", text):
            return True
        return False

    def correct(
        self,
        message: str,
        answer: str,
        *,
        solution: dict[str, Any] | None = None,
        intent: str = "",
    ) -> dict[str, Any]:
        solution = dict(solution or {})
        original = (answer or "").strip()

        # Prefer structured solution when available.
        sol = str(solution.get("answer") or "").strip()
        if sol and self.needs_correction(original, quality_ok=False):
            return {
                "corrected": True,
                "answer": sol,
                "reason": "replaced_with_solution_engine",
            }

        if not self.needs_correction(original):
            return {"corrected": False, "answer": original, "reason": "ok"}

        if sol:
            return {
                "corrected": True,
                "answer": sol,
                "reason": "replaced_with_solution_engine",
            }

        return {"corrected": False, "answer": original, "reason": "leave_to_brain"}
