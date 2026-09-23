"""Self-learning façade → self_improvement."""
from __future__ import annotations

from typing import Any

__all__ = ["note_turn", "FeedbackEngine", "FailureDetector", "EvaluationEngine", "ImprovementMemory"]


def note_turn(user: str, answer: str, *, emotion: str = "") -> None:
    try:
        from om_ai.core.self_improvement.improvement_memory import ImprovementMemory

        mem = ImprovementMemory()
        if hasattr(mem, "remember"):
            mem.remember({"user": user[:400], "answer": answer[:400], "emotion": emotion})
        elif hasattr(mem, "add"):
            mem.add(user[:200], answer[:200])
    except Exception:
        pass
    try:
        from pathlib import Path
        import json
        import time

        root = Path("artifacts") / "companion" / "self_learning"
        root.mkdir(parents=True, exist_ok=True)
        with (root / "turns.jsonl").open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "ts": time.time(),
                        "user": (user or "")[:400],
                        "answer": (answer or "")[:400],
                        "emotion": emotion,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception:
        pass


class FeedbackEngine:
    def observe(self, user: str, answer: str) -> None:
        note_turn(user, answer)


class FailureDetector:
    def check(self, answer: str) -> dict[str, Any]:
        low = (answer or "").lower()
        bad = any(
            p in low
            for p in (
                "how can i help you",
                "as an ai",
                "i don't know how to",
                "solve:",
            )
        )
        return {"failed": bad, "reason": "robotic_or_stub" if bad else ""}


class EvaluationEngine:
    def score(self, user: str, answer: str) -> dict[str, Any]:
        fail = FailureDetector().check(answer)
        return {"ok": not fail["failed"], **fail}


class ImprovementMemory:
    def remember(self, row: dict[str, Any]) -> None:
        note_turn(str(row.get("user") or ""), str(row.get("answer") or ""), emotion=str(row.get("emotion") or ""))
