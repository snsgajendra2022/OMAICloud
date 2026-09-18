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

        # Intent-aware repair
        if intent in {"greeting", "morning", "evening", "afternoon"}:
            fixed = "Hello! How can I help you today?"
            if "morning" in (message or "").lower():
                fixed = "Good morning! How can I help you today?"
            return {"corrected": True, "answer": fixed, "reason": "greeting_repair"}

        if intent == "debugging" or self._looks_debug(message):
            fixed = sol or (
                "Let's debug this.\n\n"
                "1. Copy the exact error from the console/logs.\n"
                "2. Note what changed right before it broke.\n"
                "3. Test a minimal version of the failing part.\n\n"
                "Paste the error text and I’ll give a concrete fix."
            )
            return {"corrected": True, "answer": fixed, "reason": "debug_repair"}

        fixed = sol or (
            "Here’s a clearer take:\n\n"
            f"You asked: {(message or '').strip()[:180]}\n\n"
            "I can help with a direct answer, steps, or code — "
            "tell me which you prefer if this isn’t enough."
        )
        return {"corrected": True, "answer": fixed, "reason": "generic_repair"}

    def _looks_debug(self, message: str) -> bool:
        low = (message or "").lower()
        return any(
            w in low
            for w in ("error", "bug", "blank page", "crash", "not working", "broken")
        )
