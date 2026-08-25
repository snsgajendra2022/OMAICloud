"""Evaluation framework — scorer + reports + improvement hooks."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from om_ai.eval.platform import run_suite


def score_dimensions(result: dict[str, Any]) -> dict[str, float]:
    """Map suite categories to 0–100 dimension scores."""
    by = result.get("by_category") or {}
    dims = {
        "coding": by.get("coding", {}).get("accuracy", 0.0) * 100,
        "architecture": by.get("reasoning", {}).get("accuracy", 0.0) * 100,
        "reasoning": by.get("reasoning", {}).get("accuracy", 0.0) * 100,
        "security": by.get("safety", {}).get("accuracy", 0.0) * 100,
        "completeness": float(result.get("accuracy") or 0.0) * 100,
        "math": by.get("math", {}).get("accuracy", 0.0) * 100,
        "knowledge": by.get("knowledge", {}).get("accuracy", 0.0) * 100,
        "agents": by.get("agent", {}).get("accuracy", 0.0) * 100,
        "long_context": by.get("long_context", {}).get("accuracy", 0.0) * 100,
    }
    return {k: round(v, 1) for k, v in dims.items()}


def write_report(result: dict[str, Any], path: str | Path) -> dict[str, Any]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    scores = score_dimensions(result)
    weak = [k for k, v in scores.items() if v < 70]
    report = {
        "generated_at": time.time(),
        "scores": scores,
        "summary": {
            "total": result.get("total"),
            "passed": result.get("passed"),
            "accuracy": result.get("accuracy"),
            "mode": result.get("mode"),
        },
        "weak_areas": weak,
        "improvement": "Needed" if weak else "Hold / promote candidate",
        "raw": {k: v for k, v in result.items() if k != "cases"},
    }
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run_evaluation(
    *,
    out: str | Path = "artifacts/eval/foundation_report.json",
    feed_learning: bool = True,
) -> dict[str, Any]:
    result = run_suite(report_path=None)
    report = write_report(result, out)
    if feed_learning and report.get("weak_areas"):
        try:
            from om_ai.learning import run_learning_cycle

            report["learning_cycle"] = run_learning_cycle(
                out_dir="data/continuous",
                weak_areas=list(report["weak_areas"]),
                synthesize_from_eval=True,
            )
        except Exception as exc:
            report["learning_cycle_error"] = str(exc)
    return report
