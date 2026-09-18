"""Bridge to companion_memory."""
from __future__ import annotations

from typing import Any

from om_ai.core.companion_memory import get_memory_service


class MemoryBridge:
    def __init__(self) -> None:
        self._svc = get_memory_service()

    @property
    def disabled(self) -> bool:
        return self._svc.disable_memory

    def recall(
        self,
        query: str,
        *,
        session_key: str,
        user_key: str,
        project_key: str = "",
    ) -> dict[str, Any]:
        return self._svc.recall(
            query,
            session_key=session_key,
            user_key=user_key,
            project_key=project_key,
        )

    def remember_turn(
        self,
        *,
        session_key: str,
        user_key: str,
        role: str,
        content: str,
        intent: str = "",
        project_key: str = "",
        confidence: float = 0.0,
    ) -> dict[str, Any]:
        return self._svc.remember_turn(
            session_key=session_key,
            user_key=user_key,
            role=role,
            content=content,
            intent=intent,
            project_key=project_key,
            confidence=confidence,
        )

    def list_memory(
        self,
        *,
        session_key: str = "",
        user_key: str = "",
        project_key: str = "",
    ) -> dict[str, Any]:
        return self._svc.list_all(
            session_key=session_key,
            user_key=user_key,
            project_key=project_key,
        )

    def clear_memory(self, **kwargs: Any) -> dict[str, Any]:
        return self._svc.clear(**kwargs)
