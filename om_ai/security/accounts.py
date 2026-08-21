"""User accounts + login sessions (SQLite).

Database path (set in .env):
  OM_AI_ACCOUNTS_DB=artifacts/accounts.sqlite3

Passwords use stdlib scrypt. Session secrets are hashed like API tokens
(SHA-256) and returned once at register/login.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from om_ai.security.auth import VALID_ROLES

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DEFAULT_SESSION_DAYS = 30


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: datetime | None = None) -> str:
    return (dt or _utc_now()).isoformat()


def _hash_secret(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """scrypt password hash: scrypt$n$r$p$salt_b64$hash_b64."""
    import base64

    n, r, p = 2**14, 8, 1
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=32,
    )
    return "scrypt${}${}${}${}${}".format(
        n,
        r,
        p,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    import base64

    try:
        kind, n_s, r_s, p_s, salt_b64, hash_b64 = encoded.split("$", 5)
        if kind != "scrypt":
            return False
        n, r, p = int(n_s), int(r_s), int(p_s)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(hash_b64.encode("ascii"))
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
        )
        return hmac.compare_digest(digest, expected)
    except Exception:
        return False


class AccountStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or os.getenv("OM_AI_ACCOUNTS_DB", "artifacts/accounts.sqlite3")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL DEFAULT 'default',
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'agent',
                display_name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                disabled_at TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                prefix TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                last_used_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_sessions_hash ON sessions(token_hash);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            """
        )
        self._conn.commit()

    def _normalize_email(self, email: str) -> str:
        return (email or "").strip().lower()

    def _validate_email(self, email: str) -> str:
        email = self._normalize_email(email)
        if not email or len(email) > 254 or not _EMAIL_RE.match(email):
            raise ValueError("Enter a valid email address.")
        return email

    def _validate_password(self, password: str) -> str:
        password = password or ""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if len(password) > 128:
            raise ValueError("Password is too long.")
        return password

    def _user_public(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "email": row["email"],
            "role": row["role"],
            "display_name": row["display_name"] or row["email"].split("@")[0],
            "tenant_id": row["tenant_id"],
            "created_at": row["created_at"],
        }

    def _issue_session(self, user_id: str, *, days: int | None = None) -> dict[str, Any]:
        days = days if days is not None else int(
            os.getenv("OM_AI_SESSION_DAYS", str(_DEFAULT_SESSION_DAYS))
        )
        token = secrets.token_urlsafe(32)
        session_id = secrets.token_hex(8)
        now = _utc_now()
        expires = now + timedelta(days=max(1, days))
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO sessions
                (id, user_id, token_hash, prefix, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    _hash_secret(token),
                    token[:8],
                    _utc_iso(now),
                    _utc_iso(expires),
                ),
            )
            self._conn.commit()
        return {
            "session_id": session_id,
            "token": token,
            "prefix": token[:8],
            "expires_at": _utc_iso(expires),
        }

    def register(
        self,
        email: str,
        password: str,
        *,
        display_name: str = "",
        role: str = "agent",
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        email = self._validate_email(email)
        password = self._validate_password(password)
        role = (role or "agent").strip().lower()
        if role not in VALID_ROLES:
            raise ValueError(f"role must be one of: {sorted(VALID_ROLES)}")
        # Self-serve signup never grants admin.
        if role == "admin":
            role = "agent"
        name = (display_name or "").strip()[:80]
        if not name:
            name = email.split("@")[0]
        user_id = secrets.token_hex(8)
        created = _utc_iso()
        with self._lock:
            try:
                self._conn.execute(
                    """
                    INSERT INTO users
                    (id, tenant_id, email, password_hash, role, display_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        tenant_id or "default",
                        email,
                        hash_password(password),
                        role,
                        name,
                        created,
                    ),
                )
                self._conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError("An account with this email already exists.") from exc
            row = self._conn.execute(
                "SELECT * FROM users WHERE id=?", (user_id,)
            ).fetchone()
        session = self._issue_session(user_id)
        return {
            "user": self._user_public(row),
            "token": session["token"],
            "session_id": session["session_id"],
            "expires_at": session["expires_at"],
            "note": "Save this session token. Use it as your API Bearer key.",
        }

    def login(self, email: str, password: str) -> dict[str, Any]:
        email = self._validate_email(email)
        password = password or ""
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM users WHERE email=?", (email,)
            ).fetchone()
        if not row or row["disabled_at"]:
            raise ValueError("Invalid email or password.")
        if not verify_password(password, row["password_hash"]):
            raise ValueError("Invalid email or password.")
        session = self._issue_session(row["id"])
        return {
            "user": self._user_public(row),
            "token": session["token"],
            "session_id": session["session_id"],
            "expires_at": session["expires_at"],
            "note": "Save this session token. Use it as your API Bearer key.",
        }

    def logout(self, raw_token: str) -> dict[str, Any]:
        if not raw_token:
            return {"revoked": False}
        digest = _hash_secret(raw_token)
        with self._lock:
            row = self._conn.execute(
                "SELECT id, revoked_at FROM sessions WHERE token_hash=?",
                (digest,),
            ).fetchone()
            if not row:
                return {"revoked": False, "reason": "unknown"}
            if row["revoked_at"]:
                return {"revoked": True, "already": True}
            now = _utc_iso()
            self._conn.execute(
                "UPDATE sessions SET revoked_at=? WHERE id=?",
                (now, row["id"]),
            )
            self._conn.commit()
        return {"revoked": True, "revoked_at": now}

    def logout_all(self, user_id: str) -> dict[str, Any]:
        now = _utc_iso()
        with self._lock:
            cur = self._conn.execute(
                """
                UPDATE sessions SET revoked_at=?
                WHERE user_id=? AND revoked_at IS NULL
                """,
                (now, user_id),
            )
            self._conn.commit()
        return {"revoked": True, "count": cur.rowcount, "revoked_at": now}

    def validate_session(self, raw_token: str) -> Optional[dict[str, Any]]:
        """Return auth info if session token is valid."""
        if not raw_token:
            return None
        digest = _hash_secret(raw_token)
        with self._lock:
            row = self._conn.execute(
                """
                SELECT s.id AS session_id, s.expires_at, s.revoked_at,
                       u.id AS user_id, u.email, u.role, u.tenant_id,
                       u.display_name, u.disabled_at
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash=?
                """,
                (digest,),
            ).fetchone()
            if not row:
                return None
            if row["revoked_at"] or row["disabled_at"]:
                return None
            try:
                expires = datetime.fromisoformat(row["expires_at"])
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
                if expires <= _utc_now():
                    return None
            except Exception:
                return None
            try:
                self._conn.execute(
                    "UPDATE sessions SET last_used_at=? WHERE id=?",
                    (_utc_iso(), row["session_id"]),
                )
                self._conn.commit()
            except sqlite3.OperationalError as exc:
                logger.warning("session last_used_at update skipped: %s", exc)
                try:
                    self._conn.rollback()
                except sqlite3.Error:
                    pass
        return {
            "id": row["user_id"],
            "session_id": row["session_id"],
            "name": row["email"],
            "email": row["email"],
            "display_name": row["display_name"] or row["email"].split("@")[0],
            "role": row["role"],
            "tenant_id": row["tenant_id"],
            "source": "session",
        }

    def get_user(self, user_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM users WHERE id=?", (user_id,)
            ).fetchone()
        if not row or row["disabled_at"]:
            return None
        return self._user_public(row)


_store: AccountStore | None = None
_store_lock = threading.Lock()


def get_account_store() -> AccountStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = AccountStore()
    return _store
