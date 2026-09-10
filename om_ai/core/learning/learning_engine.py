"""STEP 83 core LearningEngine — robust continuous learning loop."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .learning_state import LearningState


class LearningEngine:
    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[3]
        self.store = root / "data" / "om-memory" / "core_learning.jsonl"
        self.store.parent.mkdir(parents=True, exist_ok=True)

    def learn(
        self,
        question: str,
        answer: str,
        evaluation: dict[str, Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Any]:
        evaluation = evaluation if isinstance(evaluation, dict) else {}
        q = (question or "").strip()
        a = (answer or "").strip()
        score = float(evaluation.get("score") or 0.0)
        issues = list(evaluation.get("issues") or [])
        if not a:
            score = 0.0
            issues.append("empty_answer")
        elif not score:
            score = 0.75 if len(a.split()) >= 8 else 0.4

        improvements: list[str] = []
        if score < 0.55:
            improvements.append("Regenerate with clearer structure and verified facts")
        if "too_short" in issues or len(a.split()) < 8:
            improvements.append("Add detail, examples, and next steps")
        if not improvements:
            improvements.append("Reinforce successful answer pattern")

        state = LearningState(
            success=score >= 0.55 and not issues,
            score=score,
            mistakes=issues,
            improvements=improvements,
            confidence=score,
            metadata={"ts": time.time()},
        )
        state.add_experience({"question": q[:300], "answer": a[:500]})

        record = {
            "ts": time.time(),
            "question": q[:500],
            "answer": a[:1000],
            "score": score,
            "issues": issues,
            "improvements": improvements,
            "success": state.success,
        }
        with self.store.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return {
            "state": state,
            "score": score,
            "improvements": improvements,
            "feedback": {"score": score, "issues": issues},
            "pipeline_evaluation": evaluation,
        }
