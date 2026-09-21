"""Follow-up generator — continuity without FAQ spam."""
from __future__ import annotations

from typing import Any


class FollowupGenerator:
    def maybe(
        self,
        message: str,
        *,
        human: dict[str, Any] | None = None,
        turn: dict[str, Any] | None = None,
    ) -> str | None:
        human = human or {}
        turn = turn or {}
        if human.get("natural_ask") and turn.get("move") in {"listen", "ask", "encourage"}:
            return str(human["natural_ask"])
        return None
