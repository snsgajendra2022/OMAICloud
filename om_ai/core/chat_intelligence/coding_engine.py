"""Coding route helper for chat intelligence / production brain."""
from __future__ import annotations

from typing import Any

from .solution_engine import SolutionEngine


class CodingEngine:
    """Thin coding facade — delegates deep solves to SolutionEngine."""

    def __init__(self, *, solution_engine: SolutionEngine | None = None) -> None:
        self.solution_engine = solution_engine or SolutionEngine()

    def solve(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.solution_engine.solve(message, context=context)

    def respond(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> str:
        pack = self.solve(message, context=context)
        answer = str(pack.get("answer") or "").strip()
        if answer:
            return answer
        return (
            "I can help with that code. Share the error, file, or snippet "
            "and I will walk through a fix."
        )
