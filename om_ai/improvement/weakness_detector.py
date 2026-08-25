"""Detect weak areas from evaluation scores."""
from __future__ import annotations

from typing import Any


THRESHOLDS = {
    "structure": 70.0,
    "clarity": 65.0,
    "security": 70.0,
    "task_fit": 65.0,
    "code_quality": 70.0,
}


def detect_weaknesses(eval_result: dict[str, Any]) -> list[dict[str, Any]]:
    scores = eval_result.get("scores") or {}
    weak: list[dict[str, Any]] = []
    for key, thr in THRESHOLDS.items():
        val = float(scores.get(key, 100.0))
        if val < thr:
            weak.append(
                {
                    "area": key,
                    "score": val,
                    "threshold": thr,
                    "hint": _hint(key),
                }
            )
    if float(eval_result.get("overall") or 0) < 70:
        weak.append(
            {
                "area": "overall",
                "score": float(eval_result.get("overall") or 0),
                "threshold": 70.0,
                "hint": "Improve completeness and directness of the answer",
            }
        )
    # dedupe by area
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for w in weak:
        if w["area"] in seen:
            continue
        seen.add(w["area"])
        out.append(w)
    return out


def _hint(area: str) -> str:
    return {
        "structure": "Use clear sections: Understanding, Plan, Implementation, Validation",
        "clarity": "Write shorter clear sentences; avoid garbled fragments",
        "security": "Include validation, no secrets, safe auth patterns",
        "task_fit": "Address every part of the user ask explicitly",
        "code_quality": "Include runnable code blocks and tests",
    }.get(area, "Improve this dimension")
