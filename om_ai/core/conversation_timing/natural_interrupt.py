"""Natural interrupt / barge-in decisions."""
from __future__ import annotations

from typing import Any


class NaturalInterrupt:
    def decide(self, *, om_speaking: bool, user_speaking: bool, stop_intent: bool = False) -> dict[str, Any]:
        if stop_intent:
            return {"interrupt": True, "reason": "stop"}
        if om_speaking and user_speaking:
            return {"interrupt": True, "reason": "barge_in"}
        return {"interrupt": False, "reason": "none"}
