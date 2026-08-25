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
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Iterator


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def capitalize_title(text: str) -> str:
    """Capitalize the first character; leave the rest unchanged (not ``str.capitalize``)."""
    s = (text or "").strip()
    if not s:
        return s
    return s[:1].upper() + s[1:]


def _assistant_like_title(text: str) -> bool:
    """True when a sidebar title looks like an OM assistant greeting, not a user prompt."""
    s = (text or "").strip().lower()
    if not s:
        return False
    markers = (
        "i'm om ai",
        "i’m om ai",
        "i am om ai",
        "how can i help you today",
        "how can i help?",
        "नमस्ते! मैं om ai",
        "मैं om ai हूँ",
        "fire away whenever",
        "tell me what you need",
    )
    return any(m in s for m in markers)


def make_chat_title(text: str, *, max_chars: int = 48) -> str:
    """Build a sidebar title from user text (Unicode-safe character trim)."""
    s = (text or "").strip().replace("\n", " ")
    s = " ".join(s.split())
    if not s or _assistant_like_title(s):
        return ""
    chars = list(s)  # code-point aware for Devanagari / emoji
    if len(chars) > max_chars:
        s = "".join(chars[: max_chars - 1]).rstrip() + "…"
    return capitalize_title(s)



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
    user_id     TEXT,
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
    last_conversation_id TEXT,
    user_id          TEXT,
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
    user_id: str | None = None
    pinned: int = 0
    archived: int = 0
    project_id: str | None = None
    share_token: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pinned"] = bool(d.get("pinned"))
        d["archived"] = bool(d.get("archived"))
        return d


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
    last_conversation_id: str | None = None
    user_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _actor_user_id(actor: str) -> str | None:
    if actor.startswith("user:") and len(actor) > 5:
        return actor.split(":", 1)[1]
    return None


class ConversationStore:
    """Tenant/actor-scoped chat history, folders, and profile in SQLite."""

    def __init__(self, path: str = "artifacts/om_ai.sqlite3") -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        self._conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.executescript(_DDL)
        self._migrate()
        self._conn.commit()

    def _migrate(self) -> None:
        """Add account-relationship columns on existing DBs."""
        def _cols(table: str) -> set[str]:
            return {
                r[1]
                for r in self._conn.execute(f"PRAGMA table_info({table})").fetchall()
            }

        conv_cols = _cols("conversations")
        if "user_id" not in conv_cols:
            self._conn.execute("ALTER TABLE conversations ADD COLUMN user_id TEXT")
        for col, decl in (
            ("pinned", "INTEGER NOT NULL DEFAULT 0"),
            ("archived", "INTEGER NOT NULL DEFAULT 0"),
            ("project_id", "TEXT"),
            ("share_token", "TEXT"),
        ):
            if col not in _cols("conversations"):
                self._conn.execute(f"ALTER TABLE conversations ADD COLUMN {col} {decl}")
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conv_project ON conversations(tenant_id, actor, project_id)"
        )
        self._conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_conv_share ON conversations(share_token) WHERE share_token IS NOT NULL"
        )
        profile_cols = _cols("user_profiles")
        if "last_conversation_id" not in profile_cols:
            self._conn.execute(
                "ALTER TABLE user_profiles ADD COLUMN last_conversation_id TEXT"
            )
        if "user_id" not in profile_cols:
            self._conn.execute("ALTER TABLE user_profiles ADD COLUMN user_id TEXT")
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(tenant_id, user_id, updated_at DESC)"
        )
        # Backfill user_id from actor user:{id}
        self._conn.execute(
            """
            UPDATE conversations
            SET user_id = substr(actor, 6)
            WHERE user_id IS NULL AND actor LIKE 'user:%'
            """
        )
        self._conn.execute(
            """
            UPDATE user_profiles
            SET user_id = substr(actor, 6)
            WHERE user_id IS NULL AND actor LIKE 'user:%'
            """
        )
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
        name = capitalize_title(name) or "Untitled folder"
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
        name = capitalize_title(name) or "Untitled folder"
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
        project_id: str | None = None,
        include_archived: bool = False,
        archived_only: bool = False,
        pinned_only: bool = False,
    ) -> list[Conversation]:
        q = """
            SELECT c.id, c.tenant_id, c.actor, c.title, c.folder_id,
                   c.created_at, c.updated_at, c.user_id,
                   COALESCE(c.pinned, 0) AS pinned,
                   COALESCE(c.archived, 0) AS archived,
                   c.project_id, c.share_token,
                   (SELECT COUNT(*) FROM chat_messages m WHERE m.conversation_id = c.id) AS message_count,
                   (SELECT m2.content FROM chat_messages m2
                    WHERE m2.conversation_id = c.id AND m2.role = 'user'
                    ORDER BY m2.created_at ASC, m2.rowid ASC LIMIT 1) AS first_user
            FROM conversations c
            WHERE c.tenant_id = ? AND c.actor = ?
        """
        params: list[Any] = [tenant_id, actor]
        if archived_only:
            q += " AND COALESCE(c.archived, 0) = 1"
        elif not include_archived:
            q += " AND COALESCE(c.archived, 0) = 0"
        if pinned_only:
            q += " AND COALESCE(c.pinned, 0) = 1"
        if unfiled_only:
            q += " AND c.folder_id IS NULL"
        elif folder_id is not None:
            q += " AND c.folder_id = ?"
            params.append(folder_id)
        if project_id is not None:
            q += " AND c.project_id = ?"
            params.append(project_id)
        q += " ORDER BY COALESCE(c.pinned, 0) DESC, c.updated_at DESC"
        rows = self._conn.execute(q, params).fetchall()
        out: list[Conversation] = []
        repairs: list[tuple[str, str]] = []
        for r in rows:
            data = dict(r)
            first_user = str(data.pop("first_user", None) or "").strip()
            title = str(data.get("title") or "")
            if first_user and (
                not title.strip()
                or title.strip() == "New chat"
                or _assistant_like_title(title)
            ):
                fixed = make_chat_title(first_user)
                if fixed and fixed != title:
                    data["title"] = fixed
                    repairs.append((fixed, data["id"]))
            # Conversation dataclass ignores unknown keys via explicit fields only
            allowed = {f.name for f in fields(Conversation)}
            payload = {k: v for k, v in data.items() if k in allowed}
            out.append(Conversation(**payload))
        if repairs:
            with self._tx():
                for title, cid in repairs:
                    self._conn.execute(
                        "UPDATE conversations SET title = ? WHERE id = ?",
                        (title, cid),
                    )
        return out
    def create_conversation(
        self,
        tenant_id: str,
        actor: str,
        *,
        title: str = "New chat",
        folder_id: str | None = None,
    ) -> Conversation:
        title = capitalize_title(title) or "New chat"
        if folder_id:
            self.get_folder(folder_id, tenant_id, actor)
        now = _utc_now()
        cid = uuid.uuid4().hex
        uid = _actor_user_id(actor)
        with self._tx():
            self._conn.execute(
                """
                INSERT INTO conversations
                    (id, tenant_id, actor, user_id, title, folder_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (cid, tenant_id, actor, uid, title, folder_id, now, now),
            )
            self._conn.execute(
                """
                UPDATE user_profiles
                SET last_conversation_id = ?, updated_at = ?, user_id = COALESCE(user_id, ?)
                WHERE tenant_id = ? AND actor = ?
                """,
                (cid, now, uid, tenant_id, actor),
            )
        return Conversation(
            cid, tenant_id, actor, title, folder_id, now, now, 0, uid, 0, 0, None, None
        )

    def get_conversation(self, conversation_id: str, tenant_id: str, actor: str) -> Conversation:
        row = self._conn.execute(
            """
            SELECT c.id, c.tenant_id, c.actor, c.title, c.folder_id,
                   c.created_at, c.updated_at, c.user_id,
                   COALESCE(c.pinned, 0) AS pinned,
                   COALESCE(c.archived, 0) AS archived,
                   c.project_id, c.share_token,
                   (SELECT COUNT(*) FROM chat_messages m WHERE m.conversation_id = c.id) AS message_count
            FROM conversations c
            WHERE c.id = ? AND c.tenant_id = ? AND c.actor = ?
            """,
            (conversation_id, tenant_id, actor),
        ).fetchone()
        if not row:
            raise KeyError(f"Conversation not found: {conversation_id}")
        return Conversation(**dict(row))

    def get_conversation_by_share_token(self, share_token: str) -> Conversation | None:
        row = self._conn.execute(
            """
            SELECT c.id, c.tenant_id, c.actor, c.title, c.folder_id,
                   c.created_at, c.updated_at, c.user_id,
                   COALESCE(c.pinned, 0) AS pinned,
                   COALESCE(c.archived, 0) AS archived,
                   c.project_id, c.share_token,
                   (SELECT COUNT(*) FROM chat_messages m WHERE m.conversation_id = c.id) AS message_count
            FROM conversations c
            WHERE c.share_token = ?
            """,
            (share_token,),
        ).fetchone()
        return Conversation(**dict(row)) if row else None

    def set_last_conversation(
        self, tenant_id: str, actor: str, conversation_id: str | None
    ) -> UserProfile:
        uid = _actor_user_id(actor)
        now = _utc_now()
        with self._tx():
            self._conn.execute(
                """
                INSERT INTO user_profiles
                    (tenant_id, actor, display_name, avatar_initial, updated_at, last_conversation_id, user_id)
                VALUES (?, ?, '', '', ?, ?, ?)
                ON CONFLICT(tenant_id, actor) DO UPDATE SET
                    last_conversation_id = excluded.last_conversation_id,
                    updated_at = excluded.updated_at,
                    user_id = COALESCE(user_profiles.user_id, excluded.user_id)
                """,
                (tenant_id, actor, now, conversation_id, uid),
            )
        return self.get_profile(tenant_id, actor)

    def update_conversation(
        self,
        conversation_id: str,
        tenant_id: str,
        actor: str,
        *,
        title: str | None = None,
        folder_id: str | None | object = ...,
        pinned: bool | None = None,
        archived: bool | None = None,
        project_id: str | None | object = ...,
        clear_share: bool = False,
        enable_share: bool = False,
    ) -> Conversation:
        conv = self.get_conversation(conversation_id, tenant_id, actor)
        new_title = conv.title if title is None else (capitalize_title(title) or "New chat")
        if folder_id is ...:
            new_folder = conv.folder_id
        else:
            new_folder = folder_id  # type: ignore[assignment]
            if new_folder:
                self.get_folder(str(new_folder), tenant_id, actor)
        new_pinned = int(conv.pinned) if pinned is None else int(bool(pinned))
        new_archived = int(conv.archived) if archived is None else int(bool(archived))
        if project_id is ...:
            new_project = conv.project_id
        else:
            new_project = project_id  # type: ignore[assignment]
        share_token = conv.share_token
        if clear_share:
            share_token = None
        elif enable_share and not share_token:
            share_token = uuid.uuid4().hex
        now = _utc_now()
        with self._tx():
            self._conn.execute(
                """
                UPDATE conversations
                SET title = ?, folder_id = ?, pinned = ?, archived = ?,
                    project_id = ?, share_token = ?, updated_at = ?
                WHERE id = ? AND tenant_id = ? AND actor = ?
                """,
                (
                    new_title,
                    new_folder,
                    new_pinned,
                    new_archived,
                    new_project,
                    share_token,
                    now,
                    conversation_id,
                    tenant_id,
                    actor,
                ),
            )
        return self.get_conversation(conversation_id, tenant_id, actor)

    def export_conversation_markdown(
        self, conversation_id: str, tenant_id: str, actor: str
    ) -> str:
        conv = self.get_conversation(conversation_id, tenant_id, actor)
        msgs = self.list_messages(conversation_id, tenant_id, actor)
        lines = [f"# {conv.title}", "", f"_Exported { _utc_now() }_", ""]
        for m in msgs:
            role = (m.role or "user").capitalize()
            lines.append(f"## {role}")
            lines.append("")
            lines.append(m.content or "")
            lines.append("")
        return "\n".join(lines)

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
            needs_title = (
                auto_title
                and (
                    not (conv.title or "").strip()
                    or conv.title.strip() == "New chat"
                    or _assistant_like_title(conv.title)
                )
            )
            if needs_title:
                user_text = ""
                for msg in messages:
                    if msg.get("role") == "user" and str(msg.get("content") or "").strip():
                        user_text = str(msg["content"]).strip()
                        break
                if not user_text:
                    row = self._conn.execute(
                        """
                        SELECT content FROM chat_messages
                        WHERE conversation_id = ? AND role = 'user'
                        ORDER BY created_at ASC, rowid ASC
                        LIMIT 1
                        """,
                        (conversation_id,),
                    ).fetchone()
                    if row:
                        user_text = str(row["content"] or "").strip()
                titled = make_chat_title(user_text)
                if titled:
                    new_title = titled
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
            SELECT tenant_id, actor, display_name, avatar_initial, updated_at,
                   last_conversation_id, user_id
            FROM user_profiles
            WHERE tenant_id = ? AND actor = ?
            """,
            (tenant_id, actor),
        ).fetchone()
        if not row:
            return UserProfile(
                tenant_id, actor, "", "", _utc_now(), None, _actor_user_id(actor)
            )
        data = dict(row)
        return UserProfile(
            tenant_id=data["tenant_id"],
            actor=data["actor"],
            display_name=data["display_name"] or "",
            avatar_initial=data["avatar_initial"] or "",
            updated_at=data["updated_at"],
            last_conversation_id=data.get("last_conversation_id"),
            user_id=data.get("user_id") or _actor_user_id(actor),
        )

    def upsert_profile(
        self,
        tenant_id: str,
        actor: str,
        *,
        display_name: str | None = None,
        avatar_initial: str | None = None,
        last_conversation_id: str | None | object = ...,
    ) -> UserProfile:
        current = self.get_profile(tenant_id, actor)
        name = current.display_name if display_name is None else display_name.strip()[:80]
        initial = current.avatar_initial if avatar_initial is None else avatar_initial.strip()[:2].upper()
        if not initial and name:
            initial = name[0].upper()
        if last_conversation_id is ...:
            last_id = current.last_conversation_id
        else:
            last_id = last_conversation_id  # type: ignore[assignment]
        uid = current.user_id or _actor_user_id(actor)
        now = _utc_now()
        with self._tx():
            self._conn.execute(
                """
                INSERT INTO user_profiles
                    (tenant_id, actor, display_name, avatar_initial, updated_at, last_conversation_id, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, actor) DO UPDATE SET
                    display_name = excluded.display_name,
                    avatar_initial = excluded.avatar_initial,
                    updated_at = excluded.updated_at,
                    last_conversation_id = excluded.last_conversation_id,
                    user_id = COALESCE(user_profiles.user_id, excluded.user_id)
                """,
                (tenant_id, actor, name, initial, now, last_id, uid),
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
