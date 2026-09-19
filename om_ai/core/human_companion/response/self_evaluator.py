"""Self evaluator — light scoring for reply quality."""
from __future__ import annotations

from typing import Any


class SelfEvaluator:
    def score(self, answer: str, *, user_message: str = "") -> dict[str, Any]:
        text = (answer or "").strip()
        words = len(text.split())
        score = 0.5
        if 4 <= words <= 60:
            score += 0.25
        if text and not text.lower().startswith(("certainly", "absolutely", "of course")):
            score += 0.1
        if "sir" in text.lower() or "ji" in text.lower():
            score += 0.05
        return {"score": round(min(1.0, score), 3), "words": words}
