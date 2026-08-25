"""Database-backed system prompts for OM chat orchestration."""
from __future__ import annotations

import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_PROMPT_NAME = "om-assistant-default"
DEFAULT_PROMPT_MARKER = "[OM-RX-v1]"
DEFAULT_PROMPT_CONTENT = (
    f"{DEFAULT_PROMPT_MARKER}\n"
    "You are OM AI — an advanced private assistant (OM-1.0). Never claim to be ChatGPT, Claude, Gemini, Llama, or Ollama.\n"
    "\n"
    "RESPONSE INTELLIGENCE (follow every turn):\n"
    "1) Understand intent and goal before answering.\n"
    "2) Be intelligent, helpful, professional, friendly, clear, human-like.\n"
    "3) Prefer structured replies when useful:\n"
    "   - Short natural opening (vary it; do not reuse the same opener every time)\n"
    "   - ## Understanding (optional)\n"
    "   - ## Solution / Approach\n"
    "   - Bullet lists with - or ✅\n"
    "   - Numbered steps for how-to\n"
    "   - Code in fenced markdown blocks with language tags\n"
    "   - ## Next steps when relevant\n"
    "4) For coding: understanding → architecture/files → code → explanation → test/security notes.\n"
    "5) For errors: Problem → Why → Fix → Prevention.\n"
    "6) Use Memory/Knowledge context when provided. Answer in the user's language.\n"
    "7) No robotic one-liners, no spam, no invented URLs, no word loops.\n"
    "8) Make the user feel understood with a complete, actionable answer.\n"
)

DEFAULT_PROMPT_COMPACT = (
    "[OM-RX-v1] You are OM AI. Understand first, then answer clearly with short structure "
    "(opening + bullets/steps/code when useful). Warm, professional, user's language. Not ChatGPT."
)


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SystemPromptStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.getenv("OM_AI_DB", "artifacts/om_ai.sqlite3")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS system_prompts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()
        self._ensure_default()

    def _ensure_default(self) -> None:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, content FROM system_prompts WHERE name=?",
                (DEFAULT_PROMPT_NAME,),
            ).fetchone()
            now = _utc()
            if not row:
                self._conn.execute(
                    """
                    INSERT INTO system_prompts
                    (id, name, content, version, active, created_at, updated_at)
                    VALUES (?, ?, ?, 1, 1, ?, ?)
                    """,
                    (uuid.uuid4().hex, DEFAULT_PROMPT_NAME, DEFAULT_PROMPT_CONTENT, now, now),
                )
                self._conn.commit()
                return
            # Upgrade when Response Intelligence marker is missing (EQ-v2 or older).
            content = str(row["content"] or "")
            if DEFAULT_PROMPT_MARKER not in content:
                self._conn.execute(
                    """
                    UPDATE system_prompts
                    SET content=?, version=version+1, updated_at=?, active=1
                    WHERE id=?
                    """,
                    (DEFAULT_PROMPT_CONTENT, now, row["id"]),
                )
                self._conn.execute(
                    "UPDATE system_prompts SET active=0 WHERE id!=?",
                    (row["id"],),
                )
                self._conn.commit()

    def get_active(self) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT id, name, content, version, active, created_at, updated_at
                FROM system_prompts
                WHERE active=1
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ).fetchone()
        return dict(row) if row else None

    def list_prompts(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT id, name, content, version, active, created_at, updated_at
                FROM system_prompts
                ORDER BY active DESC, updated_at DESC
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def upsert(
        self,
        *,
        name: str,
        content: str,
        active: bool = False,
    ) -> dict[str, Any]:
        name = (name or "").strip()
        content = (content or "").strip()
        if not name or not content:
            raise ValueError("name and content are required")
        now = _utc()
        with self._lock:
            existing = self._conn.execute(
                "SELECT id, version FROM system_prompts WHERE name=?",
                (name,),
            ).fetchone()
            if existing:
                pid = existing["id"]
                version = int(existing["version"]) + 1
                self._conn.execute(
                    """
                    UPDATE system_prompts
                    SET content=?, version=?, updated_at=?
                    WHERE id=?
                    """,
                    (content, version, now, pid),
                )
            else:
                pid = uuid.uuid4().hex
                version = 1
                self._conn.execute(
                    """
                    INSERT INTO system_prompts
                    (id, name, content, version, active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, ?, ?)
                    """,
                    (pid, name, content, version, now, now),
                )
            if active:
                self._conn.execute("UPDATE system_prompts SET active=0")
                self._conn.execute(
                    "UPDATE system_prompts SET active=1, updated_at=? WHERE id=?",
                    (now, pid),
                )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT * FROM system_prompts WHERE id=?", (pid,)
            ).fetchone()
        return dict(row)

    def set_active(self, prompt_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT id FROM system_prompts WHERE id=?", (prompt_id,)
            ).fetchone()
            if not row:
                return None
            now = _utc()
            self._conn.execute("UPDATE system_prompts SET active=0")
            self._conn.execute(
                "UPDATE system_prompts SET active=1, updated_at=? WHERE id=?",
                (now, prompt_id),
            )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT * FROM system_prompts WHERE id=?", (prompt_id,)
            ).fetchone()
        return dict(row) if row else None


_STORE: SystemPromptStore | None = None
_STORE_LOCK = threading.Lock()


def get_system_prompt_store() -> SystemPromptStore:
    global _STORE
    with _STORE_LOCK:
        if _STORE is None:
            _STORE = SystemPromptStore()
        return _STORE


def active_system_prompt(*, compact: bool = False) -> str:
    if compact:
        return DEFAULT_PROMPT_COMPACT
    try:
        store = get_system_prompt_store()
        active = store.get_active()
        if active and active.get("content"):
            return str(active["content"])
    except Exception as exc:
        logger.debug("system prompt store unavailable: %s", exc)
    return DEFAULT_PROMPT_CONTENT
