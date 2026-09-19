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
        if semantic.get("requires_model") or mode in {"social", "assist", "listen"}:
            return {
                "engine": "chatgpt_runtime",
                "style": "conversational" if mode == "social" else (
                    "solution" if mode == "task" else "explainer"
                ),
                "use_model": True,
            }
        return {
            "engine": "chatgpt_runtime",
            "style": "balanced",
            "use_model": True,
        }
