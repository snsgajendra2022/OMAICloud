"""Named API token store (SQLite).

Database path (set in .env):
  OM_AI_TOKENS_DB=artifacts/tokens.sqlite3

Tokens are stored as SHA-256 hashes. The plaintext secret is returned
only once at creation time.
"""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from om_ai.security.auth import VALID_ROLES

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass
class TokenRecord:
    id: str
    name: str
    role: str
    prefix: str
    tenant_id: str
    created_at: str
    revoked_at: str | None = None
    last_used_at: str | None = None


class TokenStore:
    """Persistent named API tokens."""

    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.getenv("OM_AI_TOKENS_DB", "artifacts/tokens.sqlite3")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        # timeout waits on SQLITE_BUSY instead of failing auth under concurrent load.
        self._conn = sqlite3.connect(
            self.path,
            check_same_thread=False,
            timeout=30.0,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_tokens (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                prefix TEXT NOT NULL,
                tenant_id TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                revoked_at TEXT,
                last_used_at TEXT
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tokens_hash ON api_tokens(token_hash)"
        )
        self._conn.commit()

    def create(
        self,
        name: str,
        role: str = "operator",
        tenant_id: str = "default",
    ) -> dict:
        name = (name or "").strip()
        if not name:
            raise ValueError("name is required")
        if len(name) > 64:
            raise ValueError("name must be <= 64 characters")
        role = (role or "operator").strip().lower()
        if role not in VALID_ROLES:
            raise ValueError(f"role must be one of: {sorted(VALID_ROLES)}")

        token = secrets.token_urlsafe(32)
        token_id = secrets.token_hex(8)
        prefix = token[:8]
        created = _utc_now()
        with self._lock:
            try:
                self._conn.execute(
                    """
                    INSERT INTO api_tokens
                    (id, name, role, token_hash, prefix, tenant_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (token_id, name, role, _hash_token(token), prefix, tenant_id, created),
                )
                self._conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"token name already exists: {name}") from exc

        return {
            "id": token_id,
            "name": name,
            "role": role,
            "tenant_id": tenant_id,
            "prefix": prefix,
            "created_at": created,
            "token": token,  # shown once
            "label": f"{name} ({role})",
            "usage": {
                "header": f"Authorization: Bearer {token}",
                "alt_header": f"X-OM-API-Key: {token}",
                "env": {
                    "OM_API_KEY": token,
                    "OM_API_BASE": "http://127.0.0.1:8080/api/v1",
                    "OM_MODEL": os.getenv("OM_AI_MODEL_ID", "om:free"),
                },
            },
            "note": "Save the token now. It will not be shown again.",
        }

    def list(self, include_revoked: bool = False) -> list[dict]:
        with self._lock:
            if include_revoked:
                rows = self._conn.execute(
                    "SELECT id, name, role, prefix, tenant_id, created_at, revoked_at, last_used_at "
                    "FROM api_tokens ORDER BY created_at DESC"
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT id, name, role, prefix, tenant_id, created_at, revoked_at, last_used_at "
                    "FROM api_tokens WHERE revoked_at IS NULL ORDER BY created_at DESC"
                ).fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "role": r["role"],
                "label": f"{r['name']} ({r['role']})",
                "prefix": r["prefix"],
                "tenant_id": r["tenant_id"],
                "created_at": r["created_at"],
                "revoked_at": r["revoked_at"],
                "last_used_at": r["last_used_at"],
                "active": r["revoked_at"] is None,
            }
            for r in rows
        ]

    def revoke(self, token_id: str) -> dict:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name, revoked_at FROM api_tokens WHERE id=?",
                (token_id,),
            ).fetchone()
            if not row:
                raise KeyError(f"token not found: {token_id}")
            if row["revoked_at"]:
                return {"id": token_id, "name": row["name"], "revoked": True, "already": True}
            now = _utc_now()
            self._conn.execute(
                "UPDATE api_tokens SET revoked_at=? WHERE id=?",
                (now, token_id),
            )
            self._conn.commit()
        return {"id": token_id, "name": row["name"], "revoked": True, "revoked_at": now}

    def validate(self, raw_token: str) -> Optional[dict]:
        """Return {role, name, id, tenant_id} if valid active token.

        Auth must succeed even if updating last_used_at hits a lock — a locked
        write must never turn a valid key into HTTP 401.
        """
        if not raw_token:
            return None
        digest = _hash_token(raw_token)
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name, role, tenant_id, revoked_at FROM api_tokens WHERE token_hash=?",
                (digest,),
            ).fetchone()
            if not row or row["revoked_at"]:
                return None
            token_id = row["id"]
            name = row["name"]
            role = row["role"]
            tenant_id = row["tenant_id"]
            try:
                self._conn.execute(
                    "UPDATE api_tokens SET last_used_at=? WHERE id=?",
                    (_utc_now(), token_id),
                )
                self._conn.commit()
            except sqlite3.OperationalError as exc:
                logger.warning("token last_used_at update skipped: %s", exc)
                try:
                    self._conn.rollback()
                except sqlite3.Error:
                    pass
        return {
            "id": token_id,
            "name": name,
            "role": role,
            "tenant_id": tenant_id,
        }


_store: TokenStore | None = None
_store_lock = threading.Lock()


def get_token_store() -> TokenStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = TokenStore()
    return _store
