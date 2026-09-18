"""Context manager for OM Chat Intelligence."""
from __future__ import annotations

from typing import Any


class ContextManager:
    """Build a compact conversation context pack for planning/generation."""

    def build(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        preferences: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        history = list(history or [])
        preferences = dict(preferences or {})
        extra = dict(extra or {})

        prior_user = [
            str(h.get("content") or "")
            for h in history
            if str(h.get("role") or "").lower() in {"user", "human"}
        ]
        prior_assistant = [
            str(h.get("content") or "")
            for h in history
            if str(h.get("role") or "").lower() in {"assistant", "ai", "om"}
        ]

        followup = False
        if history and len((message or "").split()) <= 12:
            low = (message or "").lower().strip()
            if low.startswith(("and ", "also ", "what about", "how about", "yes", "no", "ok")):
                followup = True

        context_lines: list[str] = []
        if prior_user:
            context_lines.append("Recent user asks: " + " || ".join(prior_user[-3:])[:500])
        if prior_assistant:
            context_lines.append(
                "Last assistant reply: " + prior_assistant[-1][:300]
            )
        if preferences.get("tone"):
            context_lines.append(f"Preferred tone: {preferences.get('tone')}")
        if preferences.get("detail"):
            context_lines.append(f"Preferred detail: {preferences.get('detail')}")

        blob = "\n".join(context_lines).strip()[:2000]
        return {
            "message": (message or "").strip(),
            "history_count": len(history),
            "followup": followup,
            "prior_user": prior_user[-5:],
            "prior_assistant": prior_assistant[-3:],
            "preferences": preferences,
            "extra": extra,
            "context_blob": blob,
        }
