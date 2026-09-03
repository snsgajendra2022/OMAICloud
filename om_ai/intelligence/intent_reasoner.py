"""Dynamic intent reasoning — discovers intents beyond a fixed enum."""
from __future__ import annotations

from typing import Any


KNOWN_INTENTS = {
    "question",
    "create",
    "explain",
    "debug",
    "research",
    "plan",
    "generate",
    "compare",
    "summarize",
    "analyze",
    "calculate",
    "recommend",
    "chat",
    "create_prompt",
    "datetime",
}


class IntentReasoner:
    """Normalize understanding into a dynamic intent object."""

    def reason(self, understanding: dict[str, Any]) -> dict[str, Any]:
        raw = str(understanding.get("intent") or "question").strip().lower()
        discovered = raw not in KNOWN_INTENTS
        # Allow open vocabulary: keep unknown intents as discovered_*
        intent = raw if raw in KNOWN_INTENTS else f"discovered_{re_slug(raw)}"
        return {
            "intent": intent if not discovered else intent,
            "canonical": raw if raw in KNOWN_INTENTS else "question",
            "discovered": discovered,
            "domain": understanding.get("domain") or "general",
            "goal": understanding.get("goal") or "",
            "required_action": understanding.get("required_action") or "answer",
            "complexity": understanding.get("complexity") or "medium",
            "confidence": float(understanding.get("confidence") or 0.5),
        }


def re_slug(text: str) -> str:
    import re

    s = re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")
    return s[:48] or "custom"
