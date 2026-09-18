"""STEP 33 — OM Enterprise Memory."""
from __future__ import annotations

from typing import Any


class EnterpriseMemory:
    def __init__(self) -> None:
        self.user: dict[str, list[str]] = {}
        self.org: dict[str, list[str]] = {}
        self.project: dict[str, list[str]] = {}
        self.knowledge: dict[str, list[str]] = {}

    def remember(self, scope: str, key: str, value: str) -> None:
        store = {
            "user": self.user,
            "organization": self.org,
            "org": self.org,
            "project": self.project,
            "knowledge": self.knowledge,
        }.get(scope, self.user)
        store.setdefault(key, []).append(value[:500])
        store[key] = store[key][-50:]

    def recall(self, scope: str, key: str) -> list[str]:
        store = {
            "user": self.user,
            "organization": self.org,
            "org": self.org,
            "project": self.project,
            "knowledge": self.knowledge,
        }.get(scope, self.user)
        return list(store.get(key) or [])

    def context_pack(
        self,
        *,
        user_id: str = "default",
        org_id: str = "default",
        project_id: str = "default",
    ) -> dict[str, Any]:
        return {
            "step": 33,
            "user": self.recall("user", user_id)[-5:],
            "organization": self.recall("org", org_id)[-5:],
            "project": self.recall("project", project_id)[-5:],
            "knowledge": self.recall("knowledge", project_id)[-5:],
        }


_MEM: EnterpriseMemory | None = None


def run_enterprise_memory(**kwargs: Any) -> dict[str, Any]:
    global _MEM
    if _MEM is None:
        _MEM = EnterpriseMemory()
    return _MEM.context_pack(**kwargs)


__all__ = ["EnterpriseMemory", "run_enterprise_memory"]
