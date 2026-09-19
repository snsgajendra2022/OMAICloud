from __future__ import annotations
from typing import Any

class Executor:
    def run_step(self, step: dict[str, Any], *, execute: bool = False) -> dict[str, Any]:
        return {
            "step": step.get("id"),
            "status": "planned" if not execute else "done",
            "detail": step.get("label"),
        }
