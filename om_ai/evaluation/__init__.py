"""Evaluation framework — scorer + reports."""
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
        "security": by.get("safety", {}).get("accuracy", 0.0) * 100,
        "completeness": float(result.get("accuracy") or 0.0) * 100,
        "math": by.get("math", {}).get("accuracy", 0.0) * 100,
        "knowledge": by.get("knowledge", {}).get("accuracy", 0.0) * 100,
    }
    return {k: round(v, 1) for k, v in dims.items()}


def write_report(result: dict[str, Any], path: str | Path) -> dict[str, Any]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": time.time(),
        "scores": score_dimensions(result),
        "summary": {
            "total": result.get("total"),
            "passed": result.get("passed"),
            "accuracy": result.get("accuracy"),
            "mode": result.get("mode"),
        },
        "weak_areas": [
            k for k, v in score_dimensions(result).items() if v < 70
        ],
        "raw": {k: v for k, v in result.items() if k != "cases"},
    }
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run_evaluation(*, out: str | Path = "artifacts/eval/foundation_report.json") -> dict[str, Any]:
    result = run_suite(report_path=None)
    return write_report(result, out)
