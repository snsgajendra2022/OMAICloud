from __future__ import annotations

class HumorEngine:
    def light(self, address: str = "Sir") -> str:
        return f"Systems nominal, {address} — and still better company than a sticky note."

    def allow(self, intent: str) -> bool:
        return intent in {"greeting", "thanks", "general", "check_in"}
