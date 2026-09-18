"""STEP 27 — Answer structure templates by response type."""
from __future__ import annotations

from typing import Any


class AnswerStructure:
    """Decide and apply answer structure for ChatGPT-like replies."""

    TEMPLATES: dict[str, list[str]] = {
        "short": ["direct_answer"],
        "detailed": ["summary", "details", "next_steps"],
        "code": ["brief", "code", "notes"],
        "explanation": ["definition", "why", "example"],
        "troubleshooting": ["diagnosis", "checks", "fix", "ask_if_needed"],
        "comparison": ["criteria", "option_a", "option_b", "recommendation"],
        "step_by_step": ["goal", "steps", "verify"],
    }

    def choose(self, strategy: str = "", intent: str = "") -> str:
        s = (strategy or intent or "detailed").lower()
        if s in {"short", "direct_answer", "friendly_conversation"}:
            return "short"
        if s in {"code", "code_solution", "code_first", "coding"}:
            return "code"
        if s in {"explanation", "teaching", "explain"}:
            return "explanation"
        if s in {"technical_solution", "troubleshooting", "debugging"}:
            return "troubleshooting"
        if s in {"comparison", "compare"}:
            return "comparison"
        if s in {"step_by_step", "howto"}:
            return "step_by_step"
        return "detailed"

    def sections(self, kind: str) -> list[str]:
        return list(self.TEMPLATES.get(kind) or self.TEMPLATES["detailed"])

    def apply(self, answer: str, *, kind: str = "detailed") -> dict[str, Any]:
        text = (answer or "").strip()
        secs = self.sections(kind)
        return {
            "kind": kind,
            "sections": secs,
            "answer": text,
            "structured": bool(text) and (len(secs) > 1 or kind == "short"),
        }
