"""Production platform store: workspaces, files, library, prompts, tasks, settings, knowledge sources."""
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


_DDL = """
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS platform_files (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    workspace_id TEXT,
    project_id TEXT,
    name TEXT NOT NULL,
    mime TEXT NOT NULL DEFAULT 'text/plain',
    size INTEGER NOT NULL DEFAULT 0,
    content_text TEXT NOT NULL DEFAULT '',
    storage_path TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS library_items (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    title TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'document',
    content TEXT NOT NULL DEFAULT '',
    source_ref TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'user',
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    payload TEXT NOT NULL DEFAULT '{}',
    result TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_settings (
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    data TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, actor)
);
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'document',
    uri TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'ready',
    doc_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS explore_items (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    payload TEXT NOT NULL DEFAULT '{}',
    featured INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS memories_ui (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL NOT NULL DEFAULT 0.5,
    kind TEXT NOT NULL DEFAULT 'semantic',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS platform_tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'available',
    config_schema TEXT NOT NULL DEFAULT '{}',
    installed INTEGER NOT NULL DEFAULT 0,
    enabled INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tool_bindings (
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    config TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, actor, tool_id)
);
CREATE TABLE IF NOT EXISTS project_members (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    member_email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS instruction_versions (
    id TEXT PRIMARY KEY,
    owner_type TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ws_actor ON workspaces(tenant_id, actor, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_files_actor ON platform_files(tenant_id, actor, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_lib_actor ON library_items(tenant_id, actor, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_actor ON prompts(tenant_id, actor, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_actor ON tasks(tenant_id, actor, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_notif_actor ON notifications(tenant_id, actor, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ks_actor ON knowledge_sources(tenant_id, actor, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_mem_ui ON memories_ui(tenant_id, actor, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_proj_members ON project_members(project_id, tenant_id, actor);
"""


class PlatformStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.getenv("OM_AI_DB", "artifacts/om_ai.sqlite3")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.upload_root = Path(
            os.getenv("OM_AI_UPLOADS", "artifacts/uploads")
        )
        self.upload_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.executescript(_DDL)
        self._conn.commit()
        self._migrate_tasks()
        self._seed_explore()
        self._seed_tools()

    def _migrate_tasks(self) -> None:
        cols = {r[1] for r in self._conn.execute("PRAGMA table_info(tasks)").fetchall()}
        for col, decl in (
            ("schedule", "TEXT NOT NULL DEFAULT ''"),
            ("paused", "INTEGER NOT NULL DEFAULT 0"),
            ("kind", "TEXT NOT NULL DEFAULT 'manual'"),
        ):
            if col not in cols:
                self._conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {decl}")
        lib_cols = {r[1] for r in self._conn.execute("PRAGMA table_info(library_items)").fetchall()}
        if "favorite" not in lib_cols:
            self._conn.execute(
                "ALTER TABLE library_items ADD COLUMN favorite INTEGER NOT NULL DEFAULT 0"
            )
        file_cols = {
            r[1] for r in self._conn.execute("PRAGMA table_info(platform_files)").fetchall()
        }
        if "category" not in file_cols:
            self._conn.execute(
                "ALTER TABLE platform_files ADD COLUMN category TEXT NOT NULL DEFAULT 'document'"
            )
        self._conn.commit()

    def _seed_tools(self) -> None:
        with self._lock:
            n = self._conn.execute("SELECT COUNT(*) AS c FROM platform_tools").fetchone()["c"]
            if n:
                return
            tools = [
                ("shell", "Safe Shell", "Run allowlisted shell commands.", "installed", 1, 1, 1),
                ("knowledge_search", "Knowledge Search", "Search the knowledge base.", "installed", 1, 1, 2),
                ("openapi", "API Connector", "Discover and call OpenAPI endpoints.", "available", 0, 0, 3),
                ("web_search", "Web Search", "Search the public web (when enabled).", "available", 0, 0, 4),
                ("calculator", "Calculator", "Exact arithmetic for math queries.", "available", 0, 0, 5),
                ("code_interpreter", "Code Interpreter", "Run short analysis snippets.", "available", 0, 0, 6),
                ("file_analyzer", "File Analyzer", "Summarize uploaded files.", "available", 0, 0, 7),
            ]
            for tid, name, desc, cat, installed, enabled, order in tools:
                self._conn.execute(
                    """
                    INSERT INTO platform_tools
                    (id, name, description, category, config_schema, installed, enabled, sort_order)
                    VALUES (?, ?, ?, ?, '{}', ?, ?, ?)
                    """,
                    (tid, name, desc, cat, installed, enabled, order),
                )
            self._conn.commit()

    def _seed_explore(self) -> None:
        with self._lock:
            # Fix previously seeded escaped apostrophe titles.
            self._conn.execute(
                "UPDATE explore_items SET title=? WHERE title LIKE ?",
                ("Explain like I'm 5", "%Explain like I\\'m 5%"),
            )
            self._conn.execute(
                "UPDATE explore_items SET title=? WHERE title=?",
                ("Explain like I'm 5", "Explain like I\\'m 5"),
            )
            n = self._conn.execute("SELECT COUNT(*) AS c FROM explore_items").fetchone()["c"]
            if n:
                self._conn.commit()
                return
            seeds = [
                ("featured", "Coding Assistant", "Debug, write, and review code with OM.", '{"system_prompt":"You are a coding assistant.","model":"OM-1.0"}', 1, 1),
                ("featured", "Research Assistant", "Summarize sources and answer with citations.", '{"system_prompt":"You are a research assistant.","model":"OM-1.0"}', 1, 2),
                ("featured", "Business Writer", "Draft emails, plans, and proposals.", '{"system_prompt":"You are a business writing assistant.","model":"OM-1.0"}', 1, 3),
                ("template", "Meeting notes", "Turn rough notes into structured minutes.", '{"prompt":"Convert these notes into clear meeting minutes:\\n"}', 0, 10),
                ("template", "Explain like I'm 5", "Simplify any topic.", '{"prompt":"Explain this simply:\\n"}', 0, 11),
                ("workflow", "Document Q&A", "Upload a file, then ask questions.", '{"steps":["Upload file","Create knowledge source","Chat"]}', 0, 20),
                ("workflow", "Weekly review", "Summarize chats into action items.", '{"steps":["Open History","Select chats","Ask OM to summarize"]}', 0, 21),
                ("community", "Local OM workspace", "Private, on-device OM-1.0 assistant.", '{"note":"Runs natively without third-party LLM fallback."}', 1, 30),
            ]
            for cat, title, desc, payload, featured, order in seeds:
                self._conn.execute(
                    """
                    INSERT INTO explore_items
                    (id, category, title, description, payload, featured, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (uuid.uuid4().hex, cat, title, desc, payload, featured, order),
                )
            self._conn.commit()

    # --- workspaces ---
    def list_workspaces(self, tenant_id: str, actor: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM workspaces
                WHERE tenant_id=? AND actor=?
                ORDER BY updated_at DESC
                """,
                (tenant_id, actor),
            ).fetchall()
            items = [dict(r) for r in rows]
            if not items:
                return [self.create_workspace(tenant_id, actor, name="Personal")]
            return items

    def create_workspace(self, tenant_id: str, actor: str, *, name: str) -> dict[str, Any]:
        name = (name or "").strip() or "Workspace"
        wid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO workspaces (id, tenant_id, actor, name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (wid, tenant_id, actor, name[:120], now, now),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM workspaces WHERE id=?", (wid,)).fetchone()
        return dict(row)

    # --- files ---
    def list_files(self, tenant_id: str, actor: str, *, q: str = "") -> list[dict[str, Any]]:
        with self._lock:
            if q.strip():
                like = f"%{q.strip()}%"
                rows = self._conn.execute(
                    """
                    SELECT id, tenant_id, actor, workspace_id, project_id, name, mime, size,
                           substr(content_text, 1, 400) AS preview, storage_path, created_at, updated_at
                    FROM platform_files
                    WHERE tenant_id=? AND actor=? AND (name LIKE ? OR content_text LIKE ?)
                    ORDER BY updated_at DESC
                    """,
                    (tenant_id, actor, like, like),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """
                    SELECT id, tenant_id, actor, workspace_id, project_id, name, mime, size,
                           substr(content_text, 1, 400) AS preview, storage_path, created_at, updated_at
                    FROM platform_files
                    WHERE tenant_id=? AND actor=?
                    ORDER BY updated_at DESC
                    """,
                    (tenant_id, actor),
                ).fetchall()
        return [dict(r) for r in rows]

    def get_file(self, file_id: str, tenant_id: str, actor: str) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM platform_files WHERE id=? AND tenant_id=? AND actor=?",
                (file_id, tenant_id, actor),
            ).fetchone()
        if not row:
            raise KeyError("file not found")
        return dict(row)

    def create_file(
        self,
        tenant_id: str,
        actor: str,
        *,
        name: str,
        content_text: str = "",
        mime: str = "text/plain",
        raw_bytes: bytes | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        fid = uuid.uuid4().hex
        now = _utc()
        name = (name or "untitled.txt").strip()[:240]
        storage_path = ""
        size = len((content_text or "").encode("utf-8"))
        if raw_bytes is not None:
            safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)[:80]
            rel = self.upload_root / f"{fid}_{safe}"
            rel.write_bytes(raw_bytes)
            storage_path = str(rel)
            size = len(raw_bytes)
            if not content_text and mime.startswith("text"):
                try:
                    content_text = raw_bytes.decode("utf-8", errors="replace")
                except Exception:
                    content_text = ""
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO platform_files
                (id, tenant_id, actor, workspace_id, project_id, name, mime, size,
                 content_text, storage_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fid,
                    tenant_id,
                    actor,
                    workspace_id,
                    project_id,
                    name,
                    (mime or "text/plain")[:120],
                    int(size),
                    content_text[:2_000_000],
                    storage_path,
                    now,
                    now,
                ),
            )
            self._conn.commit()
        return self.get_file(fid, tenant_id, actor)

    def update_file(
        self, file_id: str, tenant_id: str, actor: str, *, name: str | None = None
    ) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM platform_files WHERE id=? AND tenant_id=? AND actor=?",
                (file_id, tenant_id, actor),
            ).fetchone()
            if not row:
                raise KeyError("file not found")
            new_name = (name if name is not None else row["name"]).strip()[:240]
            self._conn.execute(
                "UPDATE platform_files SET name=?, updated_at=? WHERE id=?",
                (new_name, _utc(), file_id),
            )
            self._conn.commit()
        return self.get_file(file_id, tenant_id, actor)

    def delete_file(self, file_id: str, tenant_id: str, actor: str) -> None:
        with self._lock:
            row = self._conn.execute(
                "SELECT storage_path FROM platform_files WHERE id=? AND tenant_id=? AND actor=?",
                (file_id, tenant_id, actor),
            ).fetchone()
            if not row:
                raise KeyError("file not found")
            path = row["storage_path"]
            self._conn.execute(
                "DELETE FROM platform_files WHERE id=? AND tenant_id=? AND actor=?",
                (file_id, tenant_id, actor),
            )
            self._conn.commit()
        if path:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass

    # --- library ---
    def list_library(self, tenant_id: str, actor: str, *, q: str = "") -> list[dict[str, Any]]:
        with self._lock:
            if q.strip():
                like = f"%{q.strip()}%"
                rows = self._conn.execute(
                    """
                    SELECT * FROM library_items
                    WHERE tenant_id=? AND actor=? AND (title LIKE ? OR content LIKE ?)
                    ORDER BY updated_at DESC
                    """,
                    (tenant_id, actor, like, like),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """
                    SELECT * FROM library_items
                    WHERE tenant_id=? AND actor=?
                    ORDER BY updated_at DESC
                    """,
                    (tenant_id, actor),
                ).fetchall()
        return [dict(r) for r in rows]

    def create_library_item(
        self,
        tenant_id: str,
        actor: str,
        *,
        title: str,
        content: str = "",
        kind: str = "document",
        source_ref: str = "",
    ) -> dict[str, Any]:
        lid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO library_items
                (id, tenant_id, actor, title, kind, content, source_ref, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lid,
                    tenant_id,
                    actor,
                    (title or "Untitled")[:200],
                    (kind or "document")[:40],
                    content[:500_000],
                    source_ref[:500],
                    now,
                    now,
                ),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM library_items WHERE id=?", (lid,)).fetchone()
        return dict(row)

    def delete_library_item(self, item_id: str, tenant_id: str, actor: str) -> None:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM library_items WHERE id=? AND tenant_id=? AND actor=?",
                (item_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("library item not found")

    # --- prompts ---
    def list_prompts(self, tenant_id: str, actor: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM prompts
                WHERE tenant_id=? AND actor=?
                ORDER BY updated_at DESC
                """,
                (tenant_id, actor),
            ).fetchall()
        return [dict(r) for r in rows]

    def create_prompt(
        self,
        tenant_id: str,
        actor: str,
        *,
        name: str,
        content: str,
        kind: str = "user",
    ) -> dict[str, Any]:
        pid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO prompts
                (id, tenant_id, actor, name, kind, content, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    pid,
                    tenant_id,
                    actor,
                    (name or "Untitled prompt")[:120],
                    (kind or "user")[:40],
                    content[:16000],
                    now,
                    now,
                ),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM prompts WHERE id=?", (pid,)).fetchone()
        return dict(row)

    def update_prompt(
        self,
        prompt_id: str,
        tenant_id: str,
        actor: str,
        *,
        name: str | None = None,
        content: str | None = None,
        kind: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM prompts WHERE id=? AND tenant_id=? AND actor=?",
                (prompt_id, tenant_id, actor),
            ).fetchone()
            if not row:
                raise KeyError("prompt not found")
            new_name = name if name is not None else row["name"]
            new_content = content if content is not None else row["content"]
            new_kind = kind if kind is not None else row["kind"]
            version = int(row["version"]) + (1 if content is not None else 0)
            self._conn.execute(
                """
                UPDATE prompts SET name=?, content=?, kind=?, version=?, updated_at=?
                WHERE id=?
                """,
                (new_name[:120], new_content[:16000], new_kind[:40], version, _utc(), prompt_id),
            )
            self._conn.commit()
            out = self._conn.execute("SELECT * FROM prompts WHERE id=?", (prompt_id,)).fetchone()
        return dict(out)

    def delete_prompt(self, prompt_id: str, tenant_id: str, actor: str) -> None:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM prompts WHERE id=? AND tenant_id=? AND actor=?",
                (prompt_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("prompt not found")

    # --- tasks ---
    def list_tasks(self, tenant_id: str, actor: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM tasks
                WHERE tenant_id=? AND actor=?
                ORDER BY updated_at DESC
                """,
                (tenant_id, actor),
            ).fetchall()
        return [dict(r) for r in rows]

    def create_task(
        self,
        tenant_id: str,
        actor: str,
        *,
        title: str,
        payload: dict | None = None,
        status: str = "pending",
    ) -> dict[str, Any]:
        tid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO tasks
                (id, tenant_id, actor, title, status, payload, result, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, '', ?, ?)
                """,
                (
                    tid,
                    tenant_id,
                    actor,
                    (title or "Task")[:200],
                    (status or "pending")[:40],
                    json.dumps(payload or {}),
                    now,
                    now,
                ),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        return dict(row)

    def update_task(
        self,
        task_id: str,
        tenant_id: str,
        actor: str,
        *,
        status: str | None = None,
        result: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM tasks WHERE id=? AND tenant_id=? AND actor=?",
                (task_id, tenant_id, actor),
            ).fetchone()
            if not row:
                raise KeyError("task not found")
            new_status = status if status is not None else row["status"]
            new_result = result if result is not None else row["result"]
            paused = 1 if new_status == "paused" else 0
            self._conn.execute(
                "UPDATE tasks SET status=?, result=?, paused=?, updated_at=? WHERE id=?",
                (new_status[:40], new_result[:100_000], paused, _utc(), task_id),
            )
            self._conn.commit()
            out = self._conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return dict(out)

    def delete_task(self, task_id: str, tenant_id: str, actor: str) -> None:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM tasks WHERE id=? AND tenant_id=? AND actor=?",
                (task_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("task not found")

    # --- notifications ---
    def list_notifications(self, tenant_id: str, actor: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM notifications
                WHERE tenant_id=? AND actor=?
                ORDER BY created_at DESC
                LIMIT 100
                """,
                (tenant_id, actor),
            ).fetchall()
        return [dict(r) for r in rows]

    def create_notification(
        self, tenant_id: str, actor: str, *, title: str, body: str = ""
    ) -> dict[str, Any]:
        nid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO notifications
                (id, tenant_id, actor, title, body, read, created_at)
                VALUES (?, ?, ?, ?, ?, 0, ?)
                """,
                (nid, tenant_id, actor, title[:200], body[:2000], now),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM notifications WHERE id=?", (nid,)).fetchone()
        return dict(row)

    def mark_notification_read(self, notif_id: str, tenant_id: str, actor: str) -> dict[str, Any]:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE notifications SET read=1 WHERE id=? AND tenant_id=? AND actor=?",
                (notif_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("notification not found")
            row = self._conn.execute(
                "SELECT * FROM notifications WHERE id=?", (notif_id,)
            ).fetchone()
        return dict(row)

    # --- settings ---
    def get_settings(self, tenant_id: str, actor: str) -> dict[str, Any]:
        defaults = {
            "appearance": "system",
            "default_model": "OM-1.0",
            "response_style": "balanced",
            "language": "en",
            "temperature": 0.7,
            "memory_enabled": True,
            "notifications_email": False,
            "notifications_push": True,
            "notifications_tasks": True,
            "privacy_history": True,
        }
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM user_settings WHERE tenant_id=? AND actor=?",
                (tenant_id, actor),
            ).fetchone()
        if not row:
            return defaults
        try:
            data = json.loads(row["data"] or "{}")
        except json.JSONDecodeError:
            data = {}
        return {**defaults, **data}

    def update_settings(self, tenant_id: str, actor: str, patch: dict[str, Any]) -> dict[str, Any]:
        current = self.get_settings(tenant_id, actor)
        merged = {**current, **(patch or {})}
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO user_settings (tenant_id, actor, data, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(tenant_id, actor) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at
                """,
                (tenant_id, actor, json.dumps(merged), now),
            )
            self._conn.commit()
        return merged

    # --- knowledge sources ---
    def list_knowledge_sources(self, tenant_id: str, actor: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM knowledge_sources
                WHERE tenant_id=? AND actor=?
                ORDER BY updated_at DESC
                """,
                (tenant_id, actor),
            ).fetchall()
        return [dict(r) for r in rows]

    def create_knowledge_source(
        self,
        tenant_id: str,
        actor: str,
        *,
        name: str,
        source_type: str = "document",
        uri: str = "",
        doc_count: int = 0,
        status: str = "ready",
    ) -> dict[str, Any]:
        kid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO knowledge_sources
                (id, tenant_id, actor, name, source_type, uri, status, doc_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kid,
                    tenant_id,
                    actor,
                    (name or "Knowledge source")[:200],
                    (source_type or "document")[:40],
                    uri[:1000],
                    (status or "ready")[:40],
                    int(doc_count),
                    now,
                    now,
                ),
            )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT * FROM knowledge_sources WHERE id=?", (kid,)
            ).fetchone()
        return dict(row)

    def delete_knowledge_source(self, source_id: str, tenant_id: str, actor: str) -> None:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM knowledge_sources WHERE id=? AND tenant_id=? AND actor=?",
                (source_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("knowledge source not found")

    # --- explore ---
    def list_explore(self, *, category: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if category:
                rows = self._conn.execute(
                    """
                    SELECT * FROM explore_items
                    WHERE category=?
                    ORDER BY featured DESC, sort_order ASC
                    """,
                    (category,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """
                    SELECT * FROM explore_items
                    ORDER BY featured DESC, sort_order ASC
                    """
                ).fetchall()
        return [dict(r) for r in rows]

    # --- memory UI ---
    def list_memories(self, tenant_id: str, actor: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM memories_ui
                WHERE tenant_id=? AND actor=?
                ORDER BY updated_at DESC
                """,
                (tenant_id, actor),
            ).fetchall()
        return [dict(r) for r in rows]

    def create_memory(
        self,
        tenant_id: str,
        actor: str,
        *,
        content: str,
        importance: float = 0.5,
        kind: str = "semantic",
    ) -> dict[str, Any]:
        mid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO memories_ui
                (id, tenant_id, actor, content, importance, kind, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    mid,
                    tenant_id,
                    actor,
                    content[:4000],
                    float(importance),
                    (kind or "semantic")[:40],
                    now,
                    now,
                ),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM memories_ui WHERE id=?", (mid,)).fetchone()
        return dict(row)

    def update_memory(
        self,
        memory_id: str,
        tenant_id: str,
        actor: str,
        *,
        content: str | None = None,
        enabled: bool | None = None,
        importance: float | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM memories_ui WHERE id=? AND tenant_id=? AND actor=?",
                (memory_id, tenant_id, actor),
            ).fetchone()
            if not row:
                raise KeyError("memory not found")
            new_content = content if content is not None else row["content"]
            new_enabled = int(enabled) if enabled is not None else int(row["enabled"])
            new_imp = float(importance) if importance is not None else float(row["importance"])
            self._conn.execute(
                """
                UPDATE memories_ui SET content=?, enabled=?, importance=?, updated_at=?
                WHERE id=?
                """,
                (new_content[:4000], new_enabled, new_imp, _utc(), memory_id),
            )
            self._conn.commit()
            out = self._conn.execute(
                "SELECT * FROM memories_ui WHERE id=?", (memory_id,)
            ).fetchone()
        return dict(out)

    def delete_memory(self, memory_id: str, tenant_id: str, actor: str) -> None:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM memories_ui WHERE id=? AND tenant_id=? AND actor=?",
                (memory_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("memory not found")

    # --- tools ---
    def list_tools(self, tenant_id: str, actor: str) -> list[dict[str, Any]]:
        with self._lock:
            catalog = self._conn.execute(
                "SELECT * FROM platform_tools ORDER BY sort_order ASC"
            ).fetchall()
            binds = {
                r["tool_id"]: dict(r)
                for r in self._conn.execute(
                    "SELECT * FROM tool_bindings WHERE tenant_id=? AND actor=?",
                    (tenant_id, actor),
                ).fetchall()
            }
        out = []
        for t in catalog:
            item = dict(t)
            b = binds.get(t["id"])
            if b:
                item["enabled"] = int(b["enabled"])
                item["installed"] = 1
                item["user_config"] = b.get("config") or "{}"
            else:
                item["user_config"] = "{}"
            item["enabled"] = bool(item.get("enabled"))
            item["installed"] = bool(item.get("installed"))
            out.append(item)
        return out

    def set_tool(
        self,
        tenant_id: str,
        actor: str,
        tool_id: str,
        *,
        enabled: bool | None = None,
        installed: bool | None = None,
        config: dict | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            tool = self._conn.execute(
                "SELECT * FROM platform_tools WHERE id=?", (tool_id,)
            ).fetchone()
            if not tool:
                raise KeyError("tool not found")
            row = self._conn.execute(
                "SELECT * FROM tool_bindings WHERE tenant_id=? AND actor=? AND tool_id=?",
                (tenant_id, actor, tool_id),
            ).fetchone()
            now = _utc()
            cur_enabled = int(row["enabled"]) if row else int(tool["enabled"])
            cur_config = row["config"] if row else "{}"
            if enabled is not None:
                cur_enabled = int(bool(enabled))
            if config is not None:
                cur_config = json.dumps(config)
            if installed is False:
                self._conn.execute(
                    "DELETE FROM tool_bindings WHERE tenant_id=? AND actor=? AND tool_id=?",
                    (tenant_id, actor, tool_id),
                )
            else:
                self._conn.execute(
                    """
                    INSERT INTO tool_bindings (tenant_id, actor, tool_id, enabled, config, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(tenant_id, actor, tool_id) DO UPDATE SET
                        enabled=excluded.enabled, config=excluded.config, updated_at=excluded.updated_at
                    """,
                    (tenant_id, actor, tool_id, cur_enabled, cur_config, now),
                )
            self._conn.commit()
        return next(t for t in self.list_tools(tenant_id, actor) if t["id"] == tool_id)

    # --- scheduled tasks helpers ---
    def create_scheduled_task(
        self,
        tenant_id: str,
        actor: str,
        *,
        title: str,
        schedule: str,
        payload: dict | None = None,
    ) -> dict[str, Any]:
        tid = uuid.uuid4().hex
        now = _utc()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO tasks
                (id, tenant_id, actor, title, status, payload, result, created_at, updated_at, schedule, paused, kind)
                VALUES (?, ?, ?, ?, 'active', ?, '', ?, ?, ?, 0, 'scheduled')
                """,
                (
                    tid,
                    tenant_id,
                    actor,
                    (title or "Scheduled task")[:200],
                    json.dumps(payload or {}),
                    now,
                    now,
                    (schedule or "daily")[:120],
                ),
            )
            self._conn.commit()
            row = self._conn.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
        return dict(row)

    def list_tasks_by_status(
        self, tenant_id: str, actor: str, *, status: str | None = None
    ) -> list[dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute(
                    """
                    SELECT * FROM tasks
                    WHERE tenant_id=? AND actor=? AND status=?
                    ORDER BY updated_at DESC
                    """,
                    (tenant_id, actor, status),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """
                    SELECT * FROM tasks
                    WHERE tenant_id=? AND actor=?
                    ORDER BY updated_at DESC
                    """,
                    (tenant_id, actor),
                ).fetchall()
        return [dict(r) for r in rows]

    # --- project members ---
    def list_project_members(
        self, project_id: str, tenant_id: str, actor: str
    ) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM project_members
                WHERE project_id=? AND tenant_id=? AND actor=?
                ORDER BY created_at DESC
                """,
                (project_id, tenant_id, actor),
            ).fetchall()
        return [dict(r) for r in rows]

    def add_project_member(
        self,
        project_id: str,
        tenant_id: str,
        actor: str,
        *,
        member_email: str,
        role: str = "viewer",
    ) -> dict[str, Any]:
        mid = uuid.uuid4().hex
        now = _utc()
        email = (member_email or "").strip().lower()
        if not email or "@" not in email:
            raise ValueError("valid member_email required")
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO project_members
                (id, project_id, tenant_id, actor, member_email, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (mid, project_id, tenant_id, actor, email[:200], (role or "viewer")[:40], now),
            )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT * FROM project_members WHERE id=?", (mid,)
            ).fetchone()
        return dict(row)

    def delete_project_member(
        self, member_id: str, tenant_id: str, actor: str
    ) -> None:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM project_members WHERE id=? AND tenant_id=? AND actor=?",
                (member_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("member not found")

    # --- instruction versions ---
    def save_instruction_version(
        self,
        tenant_id: str,
        actor: str,
        *,
        owner_type: str,
        owner_id: str,
        content: str,
    ) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT MAX(version) AS v FROM instruction_versions
                WHERE owner_type=? AND owner_id=? AND tenant_id=? AND actor=?
                """,
                (owner_type, owner_id, tenant_id, actor),
            ).fetchone()
            version = int(row["v"] or 0) + 1
            iid = uuid.uuid4().hex
            now = _utc()
            self._conn.execute(
                """
                INSERT INTO instruction_versions
                (id, owner_type, owner_id, tenant_id, actor, content, version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (iid, owner_type, owner_id, tenant_id, actor, content[:16000], version, now),
            )
            self._conn.commit()
            out = self._conn.execute(
                "SELECT * FROM instruction_versions WHERE id=?", (iid,)
            ).fetchone()
        return dict(out)

    def list_instruction_versions(
        self, tenant_id: str, actor: str, *, owner_type: str, owner_id: str
    ) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM instruction_versions
                WHERE owner_type=? AND owner_id=? AND tenant_id=? AND actor=?
                ORDER BY version DESC
                """,
                (owner_type, owner_id, tenant_id, actor),
            ).fetchall()
        return [dict(r) for r in rows]

    def set_library_favorite(
        self, item_id: str, tenant_id: str, actor: str, favorite: bool
    ) -> dict[str, Any]:
        with self._lock:
            cur = self._conn.execute(
                """
                UPDATE library_items SET favorite=?, updated_at=?
                WHERE id=? AND tenant_id=? AND actor=?
                """,
                (int(bool(favorite)), _utc(), item_id, tenant_id, actor),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                raise KeyError("library item not found")
            row = self._conn.execute(
                "SELECT * FROM library_items WHERE id=?", (item_id,)
            ).fetchone()
        return dict(row)

    def billing_snapshot(self, tenant_id: str, actor: str) -> dict[str, Any]:
        settings = self.get_settings(tenant_id, actor)
        with self._lock:
            files = self._conn.execute(
                "SELECT COUNT(*) AS c FROM platform_files WHERE tenant_id=? AND actor=?",
                (tenant_id, actor),
            ).fetchone()["c"]
            prompts = self._conn.execute(
                "SELECT COUNT(*) AS c FROM prompts WHERE tenant_id=? AND actor=?",
                (tenant_id, actor),
            ).fetchone()["c"]
            memories = self._conn.execute(
                "SELECT COUNT(*) AS c FROM memories_ui WHERE tenant_id=? AND actor=?",
                (tenant_id, actor),
            ).fetchone()["c"]
        return {
            "plan": settings.get("plan", "local"),
            "usage": {
                "files": files,
                "prompts": prompts,
                "memories": memories,
            },
            "payment": {"method": "none", "status": "local-self-hosted"},
            "limits": {"files": 10000, "prompts": 5000, "memories": 5000},
        }

    # --- global search ---
    def search_all(
        self, tenant_id: str, actor: str, q: str, *, type_filter: str = ""
    ) -> dict[str, list[dict[str, Any]]]:
        q = (q or "").strip()
        out: dict[str, list[dict[str, Any]]] = {
            "files": [],
            "library": [],
            "prompts": [],
            "projects": [],
            "assistants": [],
            "memories": [],
            "tasks": [],
        }
        if not q:
            return out
        tf = (type_filter or "").lower()
        if not tf or tf == "files":
            out["files"] = self.list_files(tenant_id, actor, q=q)[:20]
        if not tf or tf == "library":
            out["library"] = self.list_library(tenant_id, actor, q=q)[:20]
        if not tf or tf in {"prompts", "prompt"}:
            like = f"%{q}%"
            with self._lock:
                rows = self._conn.execute(
                    """
                    SELECT * FROM prompts
                    WHERE tenant_id=? AND actor=? AND (name LIKE ? OR content LIKE ?)
                    ORDER BY updated_at DESC LIMIT 20
                    """,
                    (tenant_id, actor, like, like),
                ).fetchall()
            out["prompts"] = [dict(r) for r in rows]
        if not tf or tf == "memories":
            like = f"%{q}%"
            with self._lock:
                rows = self._conn.execute(
                    """
                    SELECT * FROM memories_ui
                    WHERE tenant_id=? AND actor=? AND content LIKE ?
                    ORDER BY updated_at DESC LIMIT 20
                    """,
                    (tenant_id, actor, like),
                ).fetchall()
            out["memories"] = [dict(r) for r in rows]
        if not tf or tf == "tasks":
            like = f"%{q}%"
            with self._lock:
                rows = self._conn.execute(
                    """
                    SELECT * FROM tasks
                    WHERE tenant_id=? AND actor=? AND (title LIKE ? OR result LIKE ?)
                    ORDER BY updated_at DESC LIMIT 20
                    """,
                    (tenant_id, actor, like, like),
                ).fetchall()
            out["tasks"] = [dict(r) for r in rows]
        return out


_store: PlatformStore | None = None
_lock = threading.Lock()


def get_platform_store() -> PlatformStore:
    global _store
    if _store is None:
        with _lock:
            if _store is None:
                _store = PlatformStore()
    return _store
