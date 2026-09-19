"""Memory manager — short-term + companion MemoryService + human_memory."""
from __future__ import annotations

from typing import Any

from om_ai.core.companion_memory import get_memory_service

from .short_term_memory import ShortTermMemory
from .user_profile import UserProfile


class MemoryManager:
    def __init__(self, *, user_key: str = "default:user", session_key: str = "default") -> None:
        self.user_key = user_key
        self.session_key = session_key
        self.short = ShortTermMemory()
        self.profile = UserProfile(user_key)

    def configure(self, *, user_key: str, session_key: str) -> None:
        self.user_key = user_key
        self.session_key = session_key
        self.profile.user_key = user_key

    def recall(self, query: str) -> dict[str, Any]:
        svc = get_memory_service()
        pack = svc.recall(
            query,
            session_key=self.session_key,
            user_key=self.user_key,
        )
        hm_blob = ""
        try:
            from om_ai.core.human_memory import get_human_memory

            hm_blob = str(get_human_memory().recall_blob() or "")[:1200]
        except Exception:
            hm_blob = ""
        blob = "\n".join(
            p for p in (str(pack.get("context_blob") or "").strip(), hm_blob) if p
        )
        return {
            **pack,
            "context_blob": blob[:2500],
            "short_term": self.short.history(),
            "profile": self.profile.load(),
        }

    def remember_turn(self, user: str, assistant: str) -> None:
        self.short.add("user", user)
        self.short.add("assistant", assistant)
        svc = get_memory_service()
        try:
            svc.remember_turn(
                session_key=self.session_key,
                user_key=self.user_key,
                role="user",
                content=user,
            )
            if assistant:
                svc.remember_turn(
                    session_key=self.session_key,
                    user_key=self.user_key,
                    role="assistant",
                    content=assistant,
                )
        except Exception:
            pass
        self.profile.observe(user)

    def working_notes(self) -> list[str]:
        try:
            svc = get_memory_service()
            return [str(x) for x in (svc.working.snapshot(self.session_key) or [])][-8:]
        except Exception:
            return []
