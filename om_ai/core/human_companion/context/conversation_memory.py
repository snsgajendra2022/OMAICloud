"""Conversation memory view for context awareness."""
from __future__ import annotations

from typing import Any


class ConversationMemoryCtx:
    def snapshot(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        turns = [
            {"role": h.get("role"), "content": str(h.get("content") or "")[:200]}
            for h in (history or [])[-8:]
            if h.get("content")
        ]
        return {"turns": turns, "count": len(turns)}
