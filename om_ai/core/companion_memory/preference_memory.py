"""User preference memory."""
from __future__ import annotations

from typing import Any

from .memory_event import MemoryEvent


class PreferenceMemory:
    """Tone, detail level, and explicit user prefs."""

    KIND = "preference"

    def __init__(self, store: dict[str, list[dict[str, Any]]]) -> None:
        self._store = store

    def _bucket(self, user_key: str) -> list[dict[str, Any]]:
        return self._store.setdefault(user_key, [])

    def set_pref(
        self,
        user_key: str,
        name: str,
        value: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> MemoryEvent:
        ev = MemoryEvent(
            kind=self.KIND,
            content=f"{name}={value}",
            scope="user",
            key=name,
            tags=["preference", name],
            meta={"name": name, "value": value, **(meta or {})},
        )
        bucket = self._bucket(user_key)
        for i, row in enumerate(bucket):
            if row.get("key") == name:
                bucket[i] = ev.to_dict()
                return ev
        bucket.append(ev.to_dict())
        return ev

    def get_prefs(self, user_key: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for row in self._bucket(user_key):
            if row.get("kind") != self.KIND:
                continue
            meta = row.get("meta") or {}
            name = str(meta.get("name") or row.get("key") or "")
            val = str(meta.get("value") or "")
            if name:
                out[name] = val
        return out

    def list(self, user_key: str) -> list[dict[str, Any]]:
        return [r for r in self._bucket(user_key) if r.get("kind") == self.KIND]

    def clear(self, user_key: str) -> int:
        bucket = self._bucket(user_key)
        before = len(bucket)
        self._store[user_key] = [r for r in bucket if r.get("kind") != self.KIND]
        return before - len(self._store[user_key])
