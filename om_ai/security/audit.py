"""Append-only SQLite-backed audit log for OM AI."""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB = os.getenv("OM_AI_AUDIT_DB", "artifacts/om_ai_audit.sqlite3")

_DDL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    actor       TEXT NOT NULL,
    action      TEXT NOT NULL,
    resource    TEXT NOT NULL,
    detail_json TEXT NOT NULL DEFAULT '{}',
    request_id  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action  ON audit_log (action, created_at DESC);
"""


@dataclass(frozen=True)
class AuditEntry:
    id: str
    tenant_id: str
    actor: str
    action: str
    resource: str
    detail_json: str
    request_id: str
    created_at: str

    @property
    def detail(self) -> dict[str, Any]:
        try:
            return json.loads(self.detail_json)
        except json.JSONDecodeError:
            return {}


class AuditLog:
    """Thread-safe, append-only audit log backed by SQLite.

    The log is strictly write-once: rows are never updated or deleted.

    Example::

        log = AuditLog()
        log.record(
            tenant_id="acme",
            actor="key:abc123…",
            action="model.load",
            resource="/v1/model/load",
            detail={"config": "configs/7b.json"},
        )
        entries = log.query("acme", limit=50)
    """

    def __init__(self, db_path: str | os.PathLike = _DEFAULT_DB) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        """Return a per-thread connection with WAL journal mode."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        yield self._local.conn

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(_DDL)
            conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(
        self,
        *,
        tenant_id: str,
        actor: str,
        action: str,
        resource: str,
        detail: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Append an audit entry. Returns the new entry id."""
        entry_id = uuid.uuid4().hex
        request_id = request_id or uuid.uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        detail_json = json.dumps(detail or {}, ensure_ascii=False, default=str)

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO audit_log
                    (id, tenant_id, actor, action, resource, detail_json, request_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (entry_id, tenant_id, actor, action, resource, detail_json, request_id, created_at),
            )
            conn.commit()

        logger.debug(
            "audit: tenant=%s actor=%s action=%s resource=%s id=%s",
            tenant_id, actor, action, resource, entry_id,
        )
        return entry_id

    def query(
        self,
        tenant_id: str,
        *,
        limit: int = 100,
        action_filter: Optional[str] = None,
        actor_filter: Optional[str] = None,
    ) -> list[AuditEntry]:
        """Return the most recent audit entries for *tenant_id*."""
        sql = (
            "SELECT * FROM audit_log WHERE tenant_id = ?"
        )
        params: list[Any] = [tenant_id]

        if action_filter:
            sql += " AND action = ?"
            params.append(action_filter)
        if actor_filter:
            sql += " AND actor = ?"
            params.append(actor_filter)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, limit))

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [
            AuditEntry(
                id=r["id"],
                tenant_id=r["tenant_id"],
                actor=r["actor"],
                action=r["action"],
                resource=r["resource"],
                detail_json=r["detail_json"],
                request_id=r["request_id"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def count(self, tenant_id: str) -> int:
        """Return the total number of entries for *tenant_id*."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE tenant_id = ?", (tenant_id,)
            ).fetchone()
        return row[0] if row else 0
