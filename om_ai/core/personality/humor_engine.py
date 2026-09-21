from __future__ import annotations


class HumorEngine:
    """Light warmth — never forced jokes on stress/fatigue turns."""

    def allow(self, intent: str = "", *, emotion: str = "") -> bool:
        if emotion in {"stressed", "sad", "tired", "fatigue", "frustrated", "masked_stress"}:
            return False
        return intent in {"greeting", "thanks", "general", "check_in", "share_win", "celebrate"}

    def light(self, address: str = "Sir") -> str:
        return f"Systems nominal, {address}."

    def celebrate_bug(self) -> str:
        return "Nice! That bug was probably annoying. What was causing the issue?"
