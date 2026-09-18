"""Manage turn lifecycle and history merging."""
from __future__ import annotations

from typing import Any

from om_ai.core.chat_intelligence.conversation_memory import ConversationMemory


class TurnManager:
    def __init__(self) -> None:
        self._chat_mem = ConversationMemory()

    def session_id(self, tenant_id: str, actor: str) -> str:
        return self._chat_mem.session_id(tenant_id, actor)

    def history(
        self,
        session_id: str,
        *,
        external: list[dict[str, Any]] | None = None,
        limit: int = 14,
    ) -> list[dict[str, Any]]:
        if external is not None:
            return list(external)[-limit:]
        return self._chat_mem.history(session_id, limit=limit)

    def record(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        intent: str = "",
    ) -> None:
        self._chat_mem.add(session_id, role, content, intent=intent)

    def append_to_history(
        self,
        history: list[dict[str, Any]],
        role: str,
        content: str,
    ) -> list[dict[str, Any]]:
        out = list(history)
        out.append({"role": role, "content": content})
        return out[-40:]
