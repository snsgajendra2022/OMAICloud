"""STEP 91 — Self Improvement Engine.

Previous answer → quality → failure analysis → improvement suggestions → behavior update.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class SelfImprovementEngine:
    def __init__(self, path: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parents[3]
        self.path = Path(path or root / "data" / "om-memory" / "self_improvement.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.behaviors: dict[str, float] = {
            "prefer_structure": 0.6,
            "prefer_citations": 0.5,
            "prefer_brevity": 0.4,
            "prefer_deep_reasoning": 0.55,
        }

    def analyze_failure(self, question: str, answer: str, quality: dict[str, Any] | None = None) -> list[str]:
        quality = quality or {}
        failures = list(quality.get("issues") or [])
        text = (answer or "").strip()
        if not text:
            failures.append("empty_answer")
        if text and len(text.split()) < 8:
            failures.append("insufficient_detail")
        if "http" not in text.lower() and any(
            w in (question or "").lower() for w in ("latest", "version", "source")
        ):
            failures.append("missing_sources")
        return list(dict.fromkeys(failures))

    def suggest(self, failures: list[str]) -> list[str]:
        tips = []
        for f in failures:
            if f in {"empty_answer", "insufficient_detail"}:
                tips.append("Expand with clear sections and concrete next steps")
            elif f == "missing_sources":
                tips.append("Trigger research and attach citations")
            elif "leak" in f or "garbage" in f or "random" in f:
                tips.append("Regenerate with stricter safety filters")
            else:
                tips.append(f"Address: {f}")
        if not tips:
            tips.append("Keep successful pattern; slightly enrich examples")
        return tips

    def optimize_behavior(self, failures: list[str], success: bool) -> dict[str, float]:
        if success:
            self.behaviors["prefer_structure"] = min(0.95, self.behaviors["prefer_structure"] + 0.02)
        if "missing_sources" in failures:
            self.behaviors["prefer_citations"] = min(0.95, self.behaviors["prefer_citations"] + 0.08)
        if "insufficient_detail" in failures:
            self.behaviors["prefer_deep_reasoning"] = min(
                0.95, self.behaviors["prefer_deep_reasoning"] + 0.06
            )
            self.behaviors["prefer_brevity"] = max(0.1, self.behaviors["prefer_brevity"] - 0.05)
        return dict(self.behaviors)

    def improve(
        self,
        question: str,
        answer: str,
        quality: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        quality = quality or {}
        failures = self.analyze_failure(question, answer, quality)
        success = bool(quality.get("approved", False)) and not failures
        suggestions = self.suggest(failures)
        behaviors = self.optimize_behavior(failures, success)
        record = {
            "ts": time.time(),
            "question": (question or "")[:400],
            "success": success,
            "failures": failures,
            "suggestions": suggestions,
            "behaviors": behaviors,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {
            "step": 91,
            "success": success,
            "failures": failures,
            "suggestions": suggestions,
            "behaviors": behaviors,
        }
