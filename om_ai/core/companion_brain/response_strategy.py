"""Pick response strategy from semantic + policy."""
from __future__ import annotations

from typing import Any


class ResponseStrategy:
    def select(
        self,
        semantic: dict[str, Any],
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        mode = semantic.get("conversation_mode") or "assist"
        if policy.get("prefer_runtime_fast_path") and mode == "social":
            return {
                "engine": "chat_intelligence",
                "style": "conversational",
                "use_model": False,
            }
        if semantic.get("requires_model"):
            return {
                "engine": "chatgpt_runtime",
                "style": "solution" if mode == "task" else "explainer",
                "use_model": True,
            }
        return {
            "engine": "chatgpt_runtime",
            "style": "balanced",
            "use_model": bool(semantic.get("requires_action")),
        }
