"""Growth bridge — evaluate → weakness → training examples (self-improvement)."""
from __future__ import annotations

from typing import Any


def improve(question: str, answer: str) -> dict[str, Any]:
    try:
        from om_ai.improvement import improve_from_exchange

        return improve_from_exchange(question, answer or "", bump=True) or {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
