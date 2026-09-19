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
        server = self._chat_mem.history(session_id, limit=limit * 2)
        if external is None:
            return list(server)[-limit:]
        # Merge client + server; dedupe on (role, normalized content)
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()

        def _push(item: dict[str, Any]) -> None:
            role = str(item.get("role") or "")
            content = str(item.get("content") or "").strip()
            if not content:
                return
            key = f"{role}|{content[:240].lower()}"
            if key in seen:
                return
            seen.add(key)
            merged.append({"role": role, "content": content})

        for item in server:
            if isinstance(item, dict):
                _push(item)
        for item in external:
            if isinstance(item, dict):
                _push(item)
        return merged[-limit:]

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
