"""
Persisted chat conversations, folders, and local user profile (SQLite).

Stored alongside the main OM AI DB (``OM_AI_DB`` / ``artifacts/om_ai.sqlite3``).
Chat history is not online learning into model weights — export via feedback
for controlled SFT later.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Iterator


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


_DDL = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS chat_folders (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    actor       TEXT NOT NULL,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    actor       TEXT NOT NULL,
    title       TEXT NOT NULL DEFAULT 'New chat',
    folder_id   TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    FOREIGN KEY (folder_id) REFERENCES chat_folders(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id               TEXT PRIMARY KEY,
    conversation_id  TEXT NOT NULL,
    role             TEXT NOT NULL,
    content          TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_profiles (
    tenant_id        TEXT NOT NULL,
    actor            TEXT NOT NULL,
    display_name     TEXT NOT NULL DEFAULT '',
    avatar_initial   TEXT NOT NULL DEFAULT '',
    updated_at       TEXT NOT NULL,
    PRIMARY KEY (tenant_id, actor)
);

CREATE INDEX IF NOT EXISTS idx_conv_tenant_actor
    ON conversations(tenant_id, actor, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conv_folder
    ON conversations(folder_id);
CREATE INDEX IF NOT EXISTS idx_msg_conv
    ON chat_messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_folder_tenant_actor
    ON chat_folders(tenant_id, actor, name);
"""


@dataclass(slots=True)
class Folder:
    id: str
    tenant_id: str
    actor: str
    name: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Conversation:
    id: str
    tenant_id: str
    actor: str
    title: str
    folder_id: str | None
    created_at: str
    updated_at: str
    message_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Message:
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class UserProfile:
    tenant_id: str
    actor: str
    display_name: str
    avatar_initial: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConversationStore:
    """Tenant/actor-scoped chat history, folders, and profile in SQLite."""

    def __init__(self, path: str = "artifacts/om_ai.sqlite3") -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_DDL)
        self._conn.commit()

    @contextmanager
    def _tx(self) -> Generator[sqlite3.Connection, None, None]:
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def close(self) -> None:
        self._conn.close()

    # ── Folders ──────────────────────────────────────────────────────────────

    def list_folders(self, tenant_id: str, actor: str) -> list[Folder]:
        rows = self._conn.execute(
            """
            SELECT id, tenant_id, actor, name, created_at, updated_at
            FROM chat_folders
            WHERE tenant_id = ? AND actor = ?
            ORDER BY name COLLATE NOCASE
            """,
            (tenant_id, actor),
        ).fetchall()
        return [Folder(**dict(r)) for r in rows]

    def create_folder(self, tenant_id: str, actor: str, name: str) -> Folder:
        name = (name or "").strip() or "Untitled folder"
        now = _utc_now()
        fid = uuid.uuid4().hex
        with self._tx():
            self._conn.execute(
                """
                INSERT INTO chat_folders (id, tenant_id, actor, name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (fid, tenant_id, actor, name, now, now),
            )
        return Folder(fid, tenant_id, actor, name, now, now)

    def rename_folder(self, folder_id: str, tenant_id: str, actor: str, name: str) -> Folder:
        name = (name or "").strip() or "Untitled folder"
        now = _utc_now()
        with self._tx():
            cur = self._conn.execute(
                """
                UPDATE chat_folders SET name = ?, updated_at = ?
                WHERE id = ? AND tenant_id = ? AND actor = ?
                """,
                (name, now, folder_id, tenant_id, actor),
            )
            if cur.rowcount == 0:
                raise KeyError(f"Folder not found: {folder_id}")
        return self.get_folder(folder_id, tenant_id, actor)

    def delete_folder(self, folder_id: str, tenant_id: str, actor: str) -> None:
        with self._tx():
            self._conn.execute(
                """
                UPDATE conversations SET folder_id = NULL, updated_at = ?
                WHERE folder_id = ? AND tenant_id = ? AND actor = ?
                """,
                (_utc_now(), folder_id, tenant_id, actor),
            )
            cur = self._conn.execute(
                """
                DELETE FROM chat_folders
                WHERE id = ? AND tenant_id = ? AND actor = ?
                """,
                (folder_id, tenant_id, actor),
            )
            if cur.rowcount == 0:
                raise KeyError(f"Folder not found: {folder_id}")

    def get_folder(self, folder_id: str, tenant_id: str, actor: str) -> Folder:
        row = self._conn.execute(
            """
            SELECT id, tenant_id, actor, name, created_at, updated_at
            FROM chat_folders
            WHERE id = ? AND tenant_id = ? AND actor = ?
            """,
            (folder_id, tenant_id, actor),
        ).fetchone()
        if not row:
            raise KeyError(f"Folder not found: {folder_id}")
        return Folder(**dict(row))

    # ── Conversations ────────────────────────────────────────────────────────

    def list_conversations(
        self,
        tenant_id: str,
        actor: str,
        *,
        folder_id: str | None = None,
        unfiled_only: bool = False,
    ) -> list[Conversation]:
        q = """
            SELECT c.id, c.tenant_id, c.actor, c.title, c.folder_id,
                   c.created_at, c.updated_at,
                   (SELECT COUNT(*) FROM chat_messages m WHERE m.conversation_id = c.id) AS message_count
            FROM conversations c
            WHERE c.tenant_id = ? AND c.actor = ?
        """
        params: list[Any] = [tenant_id, actor]
        if unfiled_only:
            q += " AND c.folder_id IS NULL"
        elif folder_id is not None:
            q += " AND c.folder_id = ?"
            params.append(folder_id)
        q += " ORDER BY c.updated_at DESC"
        rows = self._conn.execute(q, params).fetchall()
        return [Conversation(**dict(r)) for r in rows]

    def create_conversation(
        self,
        tenant_id: str,
        actor: str,
        *,
        title: str = "New chat",
        folder_id: str | None = None,
    ) -> Conversation:
        title = (title or "").strip() or "New chat"
        if folder_id:
            self.get_folder(folder_id, tenant_id, actor)
        now = _utc_now()
        cid = uuid.uuid4().hex
        with self._tx():
            self._conn.execute(
                """
                INSERT INTO conversations
                    (id, tenant_id, actor, title, folder_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (cid, tenant_id, actor, title, folder_id, now, now),
            )
        return Conversation(cid, tenant_id, actor, title, folder_id, now, now, 0)

    def get_conversation(self, conversation_id: str, tenant_id: str, actor: str) -> Conversation:
        row = self._conn.execute(
            """
            SELECT c.id, c.tenant_id, c.actor, c.title, c.folder_id,
                   c.created_at, c.updated_at,
                   (SELECT COUNT(*) FROM chat_messages m WHERE m.conversation_id = c.id) AS message_count
            FROM conversations c
            WHERE c.id = ? AND c.tenant_id = ? AND c.actor = ?
            """,
            (conversation_id, tenant_id, actor),
        ).fetchone()
        if not row:
            raise KeyError(f"Conversation not found: {conversation_id}")
        return Conversation(**dict(row))

    def update_conversation(
        self,
        conversation_id: str,
        tenant_id: str,
        actor: str,
        *,
        title: str | None = None,
        folder_id: str | None | object = ...,
    ) -> Conversation:
        conv = self.get_conversation(conversation_id, tenant_id, actor)
        new_title = conv.title if title is None else ((title or "").strip() or "New chat")
        if folder_id is ...:
            new_folder = conv.folder_id
        else:
            new_folder = folder_id  # type: ignore[assignment]
            if new_folder:
                self.get_folder(str(new_folder), tenant_id, actor)
        now = _utc_now()
        with self._tx():
            self._conn.execute(
                """
                UPDATE conversations
                SET title = ?, folder_id = ?, updated_at = ?
                WHERE id = ? AND tenant_id = ? AND actor = ?
                """,
                (new_title, new_folder, now, conversation_id, tenant_id, actor),
            )
        return self.get_conversation(conversation_id, tenant_id, actor)

    def delete_conversation(self, conversation_id: str, tenant_id: str, actor: str) -> None:
        with self._tx():
            self._conn.execute(
                "DELETE FROM chat_messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            cur = self._conn.execute(
                """
                DELETE FROM conversations
                WHERE id = ? AND tenant_id = ? AND actor = ?
                """,
                (conversation_id, tenant_id, actor),
            )
            if cur.rowcount == 0:
                raise KeyError(f"Conversation not found: {conversation_id}")

    # ── Messages ─────────────────────────────────────────────────────────────

    def list_messages(self, conversation_id: str, tenant_id: str, actor: str) -> list[Message]:
        self.get_conversation(conversation_id, tenant_id, actor)
        rows = self._conn.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM chat_messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC, rowid ASC
            """,
            (conversation_id,),
        ).fetchall()
        return [Message(**dict(r)) for r in rows]

    def append_messages(
        self,
        conversation_id: str,
        tenant_id: str,
        actor: str,
        messages: list[dict[str, str]],
        *,
        auto_title: bool = True,
    ) -> list[Message]:
        conv = self.get_conversation(conversation_id, tenant_id, actor)
        if not messages:
            return []
        now = _utc_now()
        created: list[Message] = []
        with self._tx():
            for msg in messages:
                role = str(msg.get("role") or "").strip()
                content = str(msg.get("content") or "")
                if role not in {"system", "user", "assistant"}:
                    raise ValueError(f"Invalid message role: {role}")
                mid = uuid.uuid4().hex
                self._conn.execute(
                    """
                    INSERT INTO chat_messages (id, conversation_id, role, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (mid, conversation_id, role, content, now),
                )
                created.append(Message(mid, conversation_id, role, content, now))
            new_title = conv.title
            if auto_title and (conv.title == "New chat" or not conv.title.strip()):
                for msg in messages:
                    if msg.get("role") == "user" and str(msg.get("content") or "").strip():
                        text = str(msg["content"]).strip().replace("\n", " ")
                        new_title = text[:60] + ("…" if len(text) > 60 else "")
                        break
            self._conn.execute(
                """
                UPDATE conversations SET title = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_title, now, conversation_id),
            )
        return created

    # ── Profile ──────────────────────────────────────────────────────────────

    def get_profile(self, tenant_id: str, actor: str) -> UserProfile:
        row = self._conn.execute(
            """
            SELECT tenant_id, actor, display_name, avatar_initial, updated_at
            FROM user_profiles
            WHERE tenant_id = ? AND actor = ?
            """,
            (tenant_id, actor),
        ).fetchone()
        if not row:
            return UserProfile(tenant_id, actor, "", "", _utc_now())
        return UserProfile(**dict(row))

    def upsert_profile(
        self,
        tenant_id: str,
        actor: str,
        *,
        display_name: str | None = None,
        avatar_initial: str | None = None,
    ) -> UserProfile:
        current = self.get_profile(tenant_id, actor)
        name = current.display_name if display_name is None else display_name.strip()[:80]
        initial = current.avatar_initial if avatar_initial is None else avatar_initial.strip()[:2].upper()
        if not initial and name:
            initial = name[0].upper()
        now = _utc_now()
        with self._tx():
            self._conn.execute(
                """
                INSERT INTO user_profiles (tenant_id, actor, display_name, avatar_initial, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, actor) DO UPDATE SET
                    display_name = excluded.display_name,
                    avatar_initial = excluded.avatar_initial,
                    updated_at = excluded.updated_at
                """,
                (tenant_id, actor, name, initial, now),
            )
        return self.get_profile(tenant_id, actor)

    def export_for_feedback(
        self, conversation_id: str, tenant_id: str, actor: str
    ) -> list[tuple[str, str]]:
        """Return (prompt, response) pairs from adjacent user/assistant turns."""
        msgs = self.list_messages(conversation_id, tenant_id, actor)
        pairs: list[tuple[str, str]] = []
        pending_user: str | None = None
        for m in msgs:
            if m.role == "user":
                pending_user = m.content
            elif m.role == "assistant" and pending_user is not None:
                pairs.append((pending_user, m.content))
                pending_user = None
        return pairs
