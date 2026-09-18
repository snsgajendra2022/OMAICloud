"""STEP 27 — Explanation engine for teaching-style answers."""
from __future__ import annotations

from typing import Any


class ExplanationEngine:
    def explain(self, topic: str, *, level: str = "balanced") -> dict[str, Any]:
        t = (topic or "this concept").strip()[:200]
        if level == "short":
            body = f"{t}: a clear, practical idea used to solve a specific problem."
        else:
            body = (
                f"**What it is**\n{t} is best understood as a practical concept "
                f"with a clear purpose.\n\n"
                f"**Why it matters**\nIt helps you solve real tasks with less confusion.\n\n"
                f"**Simple example**\nThink of a small everyday case where {t} shows up, "
                f"then map that to your project."
            )
        return {"topic": t, "level": level, "answer": body, "kind": "explanation"}
