"""Answer strategy."""
from __future__ import annotations

from typing import Any


class AnswerStrategy:
    def select(self, plan: dict[str, Any], *, policy: dict[str, Any] | None = None) -> dict[str, Any]:
        pol = (policy or {}).get("policy") or plan.get("goal") or "balanced_assist"
        max_s = int(plan.get("max_sentences") or 3)
        return {
            "engine": "companion_generate",
            "instruction": (
                f"Strategy={pol}. Reply in at most {max_s} short spoken sentences. "
                "Be concrete. No chatbot openers. No markdown walls."
            ),
            "policy": pol,
        }
