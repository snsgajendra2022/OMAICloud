"""Companion memory service — JSON persistence under artifacts/companion/memory.json."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from .episodic_memory import EpisodicMemory
from .memory_consolidator import MemoryConsolidator
from .memory_event import MemoryEvent
from .memory_policy import MemoryPolicy
from .memory_retriever import MemoryRetriever
from .preference_memory import PreferenceMemory
from .project_memory import ProjectMemory
from .semantic_memory import SemanticMemory
from .working_memory import WorkingMemory

_DEFAULT_PATH = "artifacts/companion/memory.json"


def _env_on(name: str, default: str = "1") -> bool:
    return (os.getenv(name) or default).strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


class MemoryService:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("OM_COMPANION_MEMORY_PATH", _DEFAULT_PATH))
        self.policy = MemoryPolicy()
        self.working = WorkingMemory()
        self.retriever = MemoryRetriever()
        self.consolidator = MemoryConsolidator()
        self._lock = threading.RLock()
        self._data: dict[str, Any] = {}
        self._load()
        self.episodic = EpisodicMemory(self._data.setdefault("episodic", {}))
        self.semantic = SemanticMemory(self._data.setdefault("semantic", {}))
        self.preferences = PreferenceMemory(self._data.setdefault("preferences", {}))
        self.project = ProjectMemory(self._data.setdefault("project", {}))

    @property
    def disable_memory(self) -> bool:
        return not _env_on("OM_COMPANION_MEMORY", "1")

    def _load(self) -> None:
        with self._lock:
            if not self.path.exists():
                self._data = {
                    "version": 1,
                    "meta": {"store": str(self.path)},
                    "episodic": {},
                    "semantic": {},
                    "preferences": {},
                    "project": {},
                }
                return
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._data = raw if isinstance(raw, dict) else {}
            except (OSError, json.JSONDecodeError):
                self._data = {
                    "version": 1,
                    "meta": {"store": str(self.path), "recovered": True},
                    "episodic": {},
                    "semantic": {},
                    "preferences": {},
                    "project": {},
                }

    def _save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._data["meta"] = {
                **dict(self._data.get("meta") or {}),
                "path": str(self.path),
            }
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp.replace(self.path)

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
        if self.disable_memory:
            return {"stored": False, "reason": "disabled"}
        ok, reason = self.policy.allow_store(content)
        if not ok:
            return {"stored": False, "reason": reason}
        safe = self.policy.sanitize_for_store(content)
        meta = {"intent": intent, "role": role, "confidence": confidence}
        ev = MemoryEvent(
            kind="turn",
            content=safe,
            scope="session",
            key=session_key,
            meta=meta,
        )
        self.working.push(session_key, ev)
        if role == "user":
            self.episodic.append(session_key, safe, tags=["turn", "user"], meta=meta)
        else:
            self.episodic.append(session_key, safe, tags=["turn", "assistant"], meta=meta)
        if project_key and role == "user":
            self.project.add_note(project_key, safe, tags=["turn"], meta=meta)
        self._save()
        return {"stored": True, "reason": reason, "id": ev.id}

    def remember_fact(
        self,
        user_key: str,
        topic: str,
        fact: str,
    ) -> dict[str, Any]:
        if self.disable_memory:
            return {"stored": False, "reason": "disabled"}
        ok, reason = self.policy.allow_store(fact)
        if not ok:
            return {"stored": False, "reason": reason}
        safe = self.policy.sanitize_for_store(fact)
        ev = self.semantic.upsert(user_key, topic, safe)
        self._save()
        return {"stored": True, "reason": reason, "id": ev.id}

    def set_preference(self, user_key: str, name: str, value: str) -> dict[str, Any]:
        if self.disable_memory:
            return {"stored": False, "reason": "disabled"}
        ok, reason = self.policy.allow_store(value, kind="preference")
        if not ok:
            return {"stored": False, "reason": reason}
        ev = self.preferences.set_pref(user_key, name, value)
        self._save()
        return {"stored": True, "reason": reason, "id": ev.id}

    def recall(
        self,
        query: str,
        *,
        session_key: str,
        user_key: str,
        project_key: str = "",
        limit: int = 8,
    ) -> dict[str, Any]:
        working = self.working.as_dicts(session_key, limit=limit)
        hits = self.retriever.retrieve(
            query,
            episodic=self.episodic.list(session_key, limit=40),
            semantic=self.semantic.list(user_key, limit=40),
            preferences=self.preferences.list(user_key),
            project=self.project.list(project_key, limit=30) if project_key else [],
            working=working,
            limit=limit,
        )
        return {
            "hits": hits,
            "context_blob": self.retriever.context_blob(hits),
            "preferences": self.preferences.get_prefs(user_key),
            "policy": self.policy.policy_summary(),
            "disabled": self.disable_memory,
        }

    def list_all(
        self,
        *,
        session_key: str = "",
        user_key: str = "",
        project_key: str = "",
    ) -> dict[str, Any]:
        return {
            "disabled": self.disable_memory,
            "path": str(self.path),
            "working": self.working.as_dicts(session_key) if session_key else [],
            "episodic": self.episodic.list(session_key) if session_key else [],
            "semantic": self.semantic.list(user_key) if user_key else [],
            "preferences": self.preferences.list(user_key) if user_key else [],
            "project": self.project.list(project_key) if project_key else [],
        }

    def clear(
        self,
        *,
        session_key: str = "",
        user_key: str = "",
        project_key: str = "",
        all_data: bool = False,
    ) -> dict[str, Any]:
        removed = {"episodic": 0, "semantic": 0, "preferences": 0, "project": 0}
        if all_data:
            with self._lock:
                self._data = {
                    "version": 1,
                    "meta": {"cleared": True},
                    "episodic": {},
                    "semantic": {},
                    "preferences": {},
                    "project": {},
                }
                self.episodic = EpisodicMemory(self._data["episodic"])
                self.semantic = SemanticMemory(self._data["semantic"])
                self.preferences = PreferenceMemory(self._data["preferences"])
                self.project = ProjectMemory(self._data["project"])
                self.working.clear_all()
                self._save()
            return {"cleared": True, "scope": "all", "removed": removed}
        if session_key:
            removed["episodic"] = self.episodic.clear(session_key)
            self.working.clear(session_key)
        if user_key:
            removed["semantic"] = self.semantic.clear(user_key)
            removed["preferences"] = self.preferences.clear(user_key)
        if project_key:
            removed["project"] = self.project.clear(project_key)
        self._save()
        return {"cleared": True, "scope": "partial", "removed": removed}

    def consolidate(self, session_key: str, user_key: str) -> dict[str, Any]:
        report = self.consolidator.consolidate_session(
            self.episodic.list(session_key, limit=80)
        )
        for item in report.get("topics") or []:
            if not isinstance(item, dict):
                continue
            self.semantic.upsert(
                user_key,
                str(item.get("topic") or "general"),
                str(item.get("fact") or ""),
            )
        self._save()
        return report


_SERVICE: MemoryService | None = None


def get_memory_service(path: str | None = None) -> MemoryService:
    global _SERVICE
    if _SERVICE is None or (path and str(_SERVICE.path) != path):
        _SERVICE = MemoryService(path=path)
    return _SERVICE
