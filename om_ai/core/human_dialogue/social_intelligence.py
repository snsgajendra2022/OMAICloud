from __future__ import annotations

class SocialIntelligence:
    """Soft social rules — listen first on distress, celebrate wins lightly."""

    def bias(self, intent: str) -> str:
        if intent in {"bad_day", "fatigue", "problem"}:
            return "listen_first"
        if intent == "greeting":
            return "warm_ready"
        return "helpful"
