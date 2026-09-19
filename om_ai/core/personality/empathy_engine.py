from __future__ import annotations

class EmpathyEngine:
    def soften(self, text: str, intent: str) -> str:
        if intent in {"bad_day", "fatigue", "emotional_support", "problem"} and text:
            return text
        return text
