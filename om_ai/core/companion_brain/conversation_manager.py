"""Manage companion conversation sessions."""
from __future__ import annotations

from typing import Any

from .conversation_session import ConversationSession
from .turn_manager import TurnManager


class ConversationManager:
    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}
        self.turns = TurnManager()

    def open(
        self,
        *,
        tenant_id: str = "default",
        actor: str = "",
        project_id: str = "",
        session_id: str | None = None,
    ) -> ConversationSession:
        sid = session_id or self.turns.session_id(tenant_id, actor)
        if sid not in self._sessions:
            self._sessions[sid] = ConversationSession(
                session_id=sid,
                tenant_id=tenant_id,
                actor=actor,
                project_id=project_id,
            )
        else:
            sess = self._sessions[sid]
            if project_id:
                sess.project_id = project_id
        return self._sessions[sid]

    def get(self, session_id: str) -> ConversationSession | None:
        return self._sessions.get(session_id)

    def history_for(
        self,
        session: ConversationSession,
        *,
        external: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        return self.turns.history(
            session.session_id,
            external=external,
        )
