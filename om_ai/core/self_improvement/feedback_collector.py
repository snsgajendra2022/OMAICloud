"""Feedback collector — user corrections and ratings."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class FeedbackCollector:
    def collect(self, user: str, answer: str, *, feedback: str = "", rating: int | None = None) -> None:
        try:
            root = Path("artifacts") / "companion" / "self_learning"
            root.mkdir(parents=True, exist_ok=True)
            with (root / "feedback.jsonl").open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "ts": time.time(),
                            "user": (user or "")[:400],
                            "answer": (answer or "")[:400],
                            "feedback": (feedback or "")[:400],
                            "rating": rating,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception:
            pass
