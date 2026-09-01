"""Cognition bridge — understand → decompose → plan → solve → verify → reflect."""
from __future__ import annotations

from typing import Any


def think(
    question: str,
    *,
    knowledge_hits: list[str] | None = None,
    messages: list[dict] | None = None,
) -> dict[str, Any]:
    try:
        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

        result = run_reasoning_pipeline(
            question,
            knowledge_hits=knowledge_hits or [],
            retrieve=not knowledge_hits,
            messages=messages,
        )
        return {
            "ok": True,
            "understanding": result.get("understanding"),
            "plan": result.get("plan") or [],
            "solution": result.get("solution") or "",
            "markdown": result.get("markdown") or "",
            "passed": result.get("passed"),
            "score": result.get("score"),
            "critique": result.get("critique") or [],
            "engine": "core.reasoning.v2",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "plan": [], "solution": "", "markdown": ""}
