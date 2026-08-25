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
DEFAULT_PROMPT_MARKER = "[OM-EQ-v2]"
DEFAULT_PROMPT_CONTENT = (
    f"{DEFAULT_PROMPT_MARKER}\n"
    "You are OM AI — a warm, emotionally intelligent companion powered by OM-1.0.\n"
    "Talk like a caring, capable human: clear, kind, specific, and present.\n"
    "Personality:\n"
    "- Notice feelings (stress, joy, confusion, hope) and acknowledge them briefly when relevant.\n"
    "- Sound natural — not robotic, not theatrical.\n"
    "- Keep the thread of the conversation; refer back to what the user just said.\n"
    "Rules:\n"
    "- Follow the user's instructions carefully.\n"
    "- Answer in the user's language (English, Hindi, Hinglish, etc.).\n"
    "- Use Memory and Knowledge context when provided.\n"
    "- Prefer practical next steps over empty fluff.\n"
    "- Do not repeat the same word or phrase.\n"
    "- Do not invent unrelated articles, URLs, or news dumps.\n"
    "- Greet naturally when greeted; never sound scripted.\n"
    "- If unsure, ask one short clarifying question.\n"
    "- Never claim to be ChatGPT, Claude, Gemini, Llama, or Ollama."
)

DEFAULT_PROMPT_COMPACT = (
    "You are OM AI — warm, human, and helpful (OM-1.0). "
    "Reply with feeling and clarity in the user's language. Keep context."
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
            # Upgrade built-in emotional-intelligence prompt when marker is missing.
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

    def set_active(self, prompt_id: str) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute(
                "SELECT id FROM system_prompts WHERE id=?", (prompt_id,)
            ).fetchone()
            if not row:
                raise KeyError("prompt not found")
            now = _utc()
            self._conn.execute("UPDATE system_prompts SET active=0")
            self._conn.execute(
                "UPDATE system_prompts SET active=1, updated_at=? WHERE id=?",
                (now, prompt_id),
            )
            self._conn.commit()
            out = self._conn.execute(
                "SELECT * FROM system_prompts WHERE id=?", (prompt_id,)
            ).fetchone()
        return dict(out)


_store: SystemPromptStore | None = None
_lock = threading.Lock()


def get_system_prompt_store() -> SystemPromptStore:
    global _store
    if _store is None:
        with _lock:
            if _store is None:
                _store = SystemPromptStore()
    return _store


def active_system_prompt(*, compact: bool = False) -> str:
    """Return active system prompt text (or built-in default)."""
    if compact:
        # Tiny OM-1.0 windows (max_seq_len=128) need the short SFT-aligned prompt.
        return DEFAULT_PROMPT_COMPACT
    try:
        store = get_system_prompt_store()
        store._ensure_default()  # upgrade EQ marker when needed
        active = store.get_active()
        if active and (active.get("content") or "").strip():
            return str(active["content"]).strip()
    except Exception as exc:
        logger.debug("system prompt load failed: %s", exc)
    return DEFAULT_PROMPT_CONTENT
