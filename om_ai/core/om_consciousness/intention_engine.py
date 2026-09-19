from __future__ import annotations
from typing import Any


class IntentionEngine:
    """Infer user intention from text + attention."""

    def infer(self, text: str, attention: dict[str, Any]) -> dict[str, Any]:
        low = (text or "").lower()
        primary = attention.get("primary") or "converse"
        intent = "converse"
        if primary == "empathy":
            intent = "emotional_support"
        elif primary == "vision":
            intent = "inspect_screen"
        elif primary == "schedule":
            intent = "create_reminder"
        elif primary == "analyze" or any(
            k in low for k in ("check my", "find why", "analyze", "prepare", "fix", "improve")
        ):
            intent = "diagnose_and_plan"
        elif any(k in low for k in ("good morning", "subah", "hello", "hey om")):
            intent = "greeting"
        return {"intent": intent, "raw": text, "confidence": 0.75 if intent != "converse" else 0.45}
