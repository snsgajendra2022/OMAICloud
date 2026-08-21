"""Lightweight workspace entities: projects & assistants (SQLite)."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class WorkspaceStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.getenv("OM_AI_DB", "artifacts/om_ai.sqlite3")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workspace_projects (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                instructions TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT 'OM-1.0',
                favorite INTEGER NOT NULL DEFAULT 0,
                archived INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS workspace_assistants (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                system_prompt TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT 'OM-1.0',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_ws_proj_actor
                ON workspace_projects(tenant_id, actor, updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_ws_asst_actor
                ON workspace_assistants(tenant_id, actor, updated_at DESC);
            """
        )
        self._conn.commit()
        self._migrate_projects()

    def _migrate_projects(self) -> None:
        cols = {r[1] for r in self._conn.execute("PRAGMA table_info(workspace_projects)").fetchall()}
        for col, decl in (
            ("model", "TEXT NOT NULL DEFAULT 'OM-1.0'"),
            ("favorite", "INTEGER NOT NULL DEFAULT 0"),
            ("archived", "INTEGER NOT NULL DEFAULT 0"),
        ):
            if col not in cols:
                self._conn.execute(f"ALTER TABLE workspace_projects ADD COLUMN {col} {decl}")
        self._conn.commit()

    def list_projects(
        self,
        tenant_id: str,
        actor: str,
        *,
        q: str = "",
        sort: str = "updated",
        filter_mode: str = "all",
    ) -> list[dict[str, Any]]:
        with self._lock:
            sql = """
                SELECT * FROM workspace_projects
                WHERE tenant_id=? AND actor=?
            """
            params: list[Any] = [tenant_id, actor]
            mode = (filter_mode or "all").strip().lower()
            if mode == "favorites":
                sql += " AND COALESCE(favorite,0)=1 AND COALESCE(archived,0)=0"
            elif mode == "archived":
                sql += " AND COALESCE(archived,0)=1"
            elif mode == "recent":
                sql += " AND COALESCE(archived,0)=0"
            else:
                sql += " AND COALESCE(archived,0)=0"
            if q.strip():
                like = f"%{q.strip()}%"
                sql += " AND (name LIKE ? OR description LIKE ? OR instructions LIKE ?)"
                params.extend([like, like, like])
            sort_key = (sort or "updated").strip().lower()
            if sort_key == "name":
                sql += " ORDER BY name COLLATE NOCASE ASC"
            elif sort_key == "created":
                sql += " ORDER BY created_at DESC"
            elif sort_key == "favorite":
                sql += " ORDER BY COALESCE(favorite,0) DESC, updated_at DESC"
            else:
                sql += " ORDER BY updated_at DESC"
            rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_project(self, project_id: str, tenant_id: str, actor: str) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT * FROM workspace_projects
                WHERE id=? AND tenant_id=? AND actor=?
                """,
                (project_id, tenant_id, actor),
            ).fetchone()
        if not row:
            raise KeyError("project not found")
        return dict(row)

    def create_project(
        self,
        tenant_id: str,
        actor: str,
        *,
        name: str,
        description: str = "",
        instructions: str = "",
        model: str = "OM-1.0",
    ) -> dict[str, Any]:
        name = (name or "").strip() or "Untitled project"
        pid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO workspace_projects
                (id, tenant_id, actor, name, description, instructions, model,
                 favorite, archived, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
                """,
                (
                    pid,
                    tenant_id,
                    actor,
                    name[:120],
                    description[:2000],
                    instructions[:8000],
                    (model or "OM-1.0")[:64],
                    now,
                    now,
                ),
            )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT * FROM workspace_projects WHERE id=?", (pid,)
            ).fetchone()
        return dict(row)

    def delete_project(self, project_id: str, tenant_id: str, actor: str) -> None:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM workspace_projects WHERE id=? AND tenant_id=? AND actor=?",
                (project_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("project not found")

    def list_assistants(self, tenant_id: str, actor: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM workspace_assistants
                WHERE tenant_id=? AND actor=?
                ORDER BY updated_at DESC
                """,
                (tenant_id, actor),
            ).fetchall()
        return [dict(r) for r in rows]

    def create_assistant(
        self,
        tenant_id: str,
        actor: str,
        *,
        name: str,
        description: str = "",
        system_prompt: str = "",
        model: str = "OM-1.0",
    ) -> dict[str, Any]:
        name = (name or "").strip() or "Untitled assistant"
        aid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO workspace_assistants
                (id, tenant_id, actor, name, description, system_prompt, model, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    aid,
                    tenant_id,
                    actor,
                    name[:120],
                    description[:2000],
                    system_prompt[:8000],
                    (model or "OM-1.0")[:64],
                    now,
                    now,
                ),
            )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT * FROM workspace_assistants WHERE id=?", (aid,)
            ).fetchone()
        return dict(row)

    def delete_assistant(self, assistant_id: str, tenant_id: str, actor: str) -> None:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM workspace_assistants WHERE id=? AND tenant_id=? AND actor=?",
                (assistant_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("assistant not found")

    def update_assistant(
        self,
        assistant_id: str,
        tenant_id: str,
        actor: str,
        *,
        name: str | None = None,
        description: str | None = None,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM workspace_assistants WHERE id=? AND tenant_id=? AND actor=?",
                (assistant_id, tenant_id, actor),
            ).fetchone()
            if not row:
                raise KeyError("assistant not found")
            self._conn.execute(
                """
                UPDATE workspace_assistants
                SET name=?, description=?, system_prompt=?, model=?, updated_at=?
                WHERE id=?
                """,
                (
                    (name if name is not None else row["name"])[:120],
                    (description if description is not None else row["description"])[:2000],
                    (system_prompt if system_prompt is not None else row["system_prompt"])[:8000],
                    (model if model is not None else row["model"])[:64],
                    _utc(),
                    assistant_id,
                ),
            )
            self._conn.commit()
            out = self._conn.execute(
                "SELECT * FROM workspace_assistants WHERE id=?", (assistant_id,)
            ).fetchone()
        return dict(out)

    def duplicate_assistant(
        self, assistant_id: str, tenant_id: str, actor: str
    ) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM workspace_assistants WHERE id=? AND tenant_id=? AND actor=?",
                (assistant_id, tenant_id, actor),
            ).fetchone()
            if not row:
                raise KeyError("assistant not found")
            src = dict(row)
        return self.create_assistant(
            tenant_id,
            actor,
            name=f"{src['name']} (copy)",
            description=src.get("description") or "",
            system_prompt=src.get("system_prompt") or "",
            model=src.get("model") or "OM-1.0",
        )

    def update_project(
        self,
        project_id: str,
        tenant_id: str,
        actor: str,
        *,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        model: str | None = None,
        favorite: bool | None = None,
        archived: bool | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM workspace_projects WHERE id=? AND tenant_id=? AND actor=?",
                (project_id, tenant_id, actor),
            ).fetchone()
            if not row:
                raise KeyError("project not found")
            fav = int(row["favorite"]) if "favorite" in row.keys() else 0
            arch = int(row["archived"]) if "archived" in row.keys() else 0
            mdl = row["model"] if "model" in row.keys() else "OM-1.0"
            if favorite is not None:
                fav = 1 if favorite else 0
            if archived is not None:
                arch = 1 if archived else 0
            self._conn.execute(
                """
                UPDATE workspace_projects
                SET name=?, description=?, instructions=?, model=?, favorite=?, archived=?, updated_at=?
                WHERE id=?
                """,
                (
                    (name if name is not None else row["name"])[:120],
                    (description if description is not None else row["description"])[:2000],
                    (instructions if instructions is not None else row["instructions"])[:8000],
                    (model if model is not None else mdl)[:64],
                    fav,
                    arch,
                    _utc(),
                    project_id,
                ),
            )
            self._conn.commit()
            out = self._conn.execute(
                "SELECT * FROM workspace_projects WHERE id=?", (project_id,)
            ).fetchone()
        return dict(out)

    def duplicate_project(
        self, project_id: str, tenant_id: str, actor: str
    ) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM workspace_projects WHERE id=? AND tenant_id=? AND actor=?",
                (project_id, tenant_id, actor),
            ).fetchone()
            if not row:
                raise KeyError("project not found")
            src = dict(row)
        return self.create_project(
            tenant_id,
            actor,
            name=f"{src['name']} (copy)",
            description=src.get("description") or "",
            instructions=src.get("instructions") or "",
            model=src.get("model") or "OM-1.0",
        )


_store: WorkspaceStore | None = None
_lock = threading.Lock()


def get_workspace_store() -> WorkspaceStore:
    global _store
    if _store is None:
        with _lock:
            if _store is None:
                _store = WorkspaceStore()
    return _store
