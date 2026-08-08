"""
Production SQLite memory store with multi-kind support, relevance search, and tenant isolation.

Memory kinds:
    conversation  — chat turns (default)
    episodic      — events the agent observed or participated in
    semantic      — facts, learned knowledge
    preference    — user/tenant preferences and settings
    entity        — named entities (people, orgs, products, …)
    task          — task records and their outcomes
    tool          — tool call observations
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

# ─── Valid memory kinds ───────────────────────────────────────────────────────

MemoryKind = Literal[
    "conversation", "episodic", "semantic", "preference", "entity", "task", "tool"
]
_VALID_KINDS: frozenset[str] = frozenset(
    {"conversation", "episodic", "semantic", "preference", "entity", "task", "tool"}
)

# ─── Schema ───────────────────────────────────────────────────────────────────

_DDL = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS memories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id   TEXT    NOT NULL,
    user_id     TEXT    NOT NULL,
    kind        TEXT    NOT NULL DEFAULT 'conversation',
    content     TEXT    NOT NULL,
    metadata    TEXT    NOT NULL DEFAULT '{}',
    provenance  TEXT    NOT NULL DEFAULT '{}',
    created_at  TEXT    NOT NULL,
    expires_at  TEXT
);
"""

_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_mem_tenant_user
    ON memories(tenant_id, user_id, kind, created_at);
CREATE INDEX IF NOT EXISTS idx_mem_expires
    ON memories(expires_at) WHERE expires_at IS NOT NULL;
"""


# ─── Data class ───────────────────────────────────────────────────────────────


@dataclass(slots=True)
class Memory:
    id: int
    tenant_id: str
    user_id: str
    kind: str
    content: str
    metadata: dict
    provenance: dict
    created_at: str
    expires_at: str | None = None


# ─── TF-relevance helpers (no numpy dep required here) ────────────────────────


_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _tfidf_score(query_tokens: list[str], doc: str, idf: dict[str, float]) -> float:
    doc_tokens = _tokenize(doc)
    tf_map = Counter(doc_tokens)
    total = max(1, sum(tf_map.values()))
    score = 0.0
    for term in query_tokens:
        if term in tf_map:
            tf = tf_map[term] / total
            score += tf * idf.get(term, math.log(2.0) + 1.0)
    return score


def _build_idf(corpus: list[str]) -> dict[str, float]:
    N = max(1, len(corpus))
    df: dict[str, int] = {}
    for doc in corpus:
        for term in set(_tokenize(doc)):
            df[term] = df.get(term, 0) + 1
    return {term: math.log((N + 1.0) / (n + 1.0)) + 1.0 for term, n in df.items()}


# ─── SQLiteMemoryStore ────────────────────────────────────────────────────────


class SQLiteMemoryStore:
    """
    Multi-kind, tenant-isolated, relevance-ranked memory store backed by SQLite.

    Backward-compatible API:
        add(tenant_id, user_id, content, kind, metadata) → id
        recent(tenant_id, user_id, limit) → list[Memory]

    Extended API:
        search(query, tenant_id, user_id, kind=None, limit) — TF-IDF relevance ranked
        get_relevant(prompt, tenant_id, user_id, limit) — convenience wrapper
        delete(memory_id, tenant_id) — scoped delete
        expire_older_than(days, tenant_id=None) — prune old records
    """

    def __init__(self, path: str = "artifacts/om_ai.sqlite3") -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._migrate()
        self._conn.executescript(_INDEX_DDL)
        self._conn.commit()

    def _migrate(self) -> None:
        """Add columns introduced after v0.2 without destroying existing data."""
        cols = {row[1] for row in self._conn.execute("PRAGMA table_info(memories)").fetchall()}
        if "expires_at" not in cols:
            self._conn.execute("ALTER TABLE memories ADD COLUMN expires_at TEXT")
        if "provenance" not in cols:
            self._conn.execute("ALTER TABLE memories ADD COLUMN provenance TEXT NOT NULL DEFAULT '{}'")
        if "kind" not in cols:
            self._conn.execute(
                "ALTER TABLE memories ADD COLUMN kind TEXT NOT NULL DEFAULT 'conversation'"
            )

    # ── Write ─────────────────────────────────────────────────────────────────

    def add(
        self,
        tenant_id: str,
        user_id: str,
        content: str,
        kind: str = "conversation",
        metadata: dict | None = None,
        provenance: dict | None = None,
        ttl_days: int | None = None,
    ) -> int:
        """
        Store a memory.

        Args:
            tenant_id: tenant scope.
            user_id: user within tenant.
            content: text to store.
            kind: one of the 7 memory kinds.
            metadata: arbitrary extra data.
            provenance: origin info (source, agent_id, task_id, …).
            ttl_days: if set, memory auto-expires after N days.

        Returns:
            Row id of the inserted memory.
        """
        if kind not in _VALID_KINDS:
            raise ValueError(f"Invalid kind {kind!r}. Valid kinds: {sorted(_VALID_KINDS)}")
        now = datetime.now(timezone.utc)
        created_at = now.isoformat()
        expires_at = (now + timedelta(days=ttl_days)).isoformat() if ttl_days else None
        cur = self._conn.execute(
            """INSERT INTO memories
               (tenant_id, user_id, kind, content, metadata, provenance, created_at, expires_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                tenant_id, user_id, kind, content,
                json.dumps(metadata or {}),
                json.dumps(provenance or {}),
                created_at, expires_at,
            ),
        )
        self._conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    # ── Read (backward-compat) ────────────────────────────────────────────────

    def recent(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        kind: str | None = None,
    ) -> list[Memory]:
        """
        Return the most recent memories in chronological order.
        Tenant-scoped. Optionally filter by kind.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        if kind:
            rows = self._conn.execute(
                """SELECT id, tenant_id, user_id, kind, content, metadata, provenance,
                          created_at, expires_at
                   FROM memories
                   WHERE tenant_id=? AND user_id=? AND kind=?
                     AND (expires_at IS NULL OR expires_at > ?)
                   ORDER BY id DESC LIMIT ?""",
                (tenant_id, user_id, kind, now_iso, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT id, tenant_id, user_id, kind, content, metadata, provenance,
                          created_at, expires_at
                   FROM memories
                   WHERE tenant_id=? AND user_id=?
                     AND (expires_at IS NULL OR expires_at > ?)
                   ORDER BY id DESC LIMIT ?""",
                (tenant_id, user_id, now_iso, limit),
            ).fetchall()
        return [self._row_to_memory(r) for r in reversed(rows)]

    # ── Search (relevance-ranked) ─────────────────────────────────────────────

    def search(
        self,
        query: str,
        tenant_id: str,
        user_id: str,
        kind: str | None = None,
        limit: int = 10,
    ) -> list[Memory]:
        """
        Return memories ranked by TF-IDF relevance to query.
        Filters are tenant + user scoped (tenant isolation enforced).
        Expired memories are excluded.

        Args:
            query: search string.
            tenant_id: tenant scope (required).
            user_id: user scope.
            kind: optional kind filter.
            limit: max results.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        if kind:
            rows = self._conn.execute(
                """SELECT id, tenant_id, user_id, kind, content, metadata, provenance,
                          created_at, expires_at
                   FROM memories
                   WHERE tenant_id=? AND user_id=? AND kind=?
                     AND (expires_at IS NULL OR expires_at > ?)
                   ORDER BY id DESC LIMIT ?""",
                (tenant_id, user_id, kind, now_iso, limit * 5),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT id, tenant_id, user_id, kind, content, metadata, provenance,
                          created_at, expires_at
                   FROM memories
                   WHERE tenant_id=? AND user_id=?
                     AND (expires_at IS NULL OR expires_at > ?)
                   ORDER BY id DESC LIMIT ?""",
                (tenant_id, user_id, now_iso, limit * 5),
            ).fetchall()

        if not rows:
            return []

        corpus = [r["content"] for r in rows]
        idf = _build_idf(corpus)
        q_tokens = _tokenize(query)

        scored = []
        for row in rows:
            score = _tfidf_score(q_tokens, row["content"], idf)
            scored.append((score, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._row_to_memory(r) for _, r in scored[:limit]]

    def get_relevant(
        self,
        prompt: str,
        tenant_id: str,
        user_id: str,
        limit: int = 10,
        kind: str | None = None,
    ) -> list[Memory]:
        """
        Convenience alias for search() — returns the most prompt-relevant memories.
        """
        return self.search(prompt, tenant_id, user_id, kind=kind, limit=limit)

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete(self, memory_id: int, tenant_id: str) -> bool:
        """
        Delete a specific memory by id.
        Tenant-scoped: a tenant can only delete its own memories.

        Returns:
            True if a row was deleted.
        """
        cur = self._conn.execute(
            "DELETE FROM memories WHERE id=? AND tenant_id=?",
            (memory_id, tenant_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def expire_older_than(self, days: int, tenant_id: str | None = None) -> int:
        """
        Hard-delete memories older than `days` days.
        If tenant_id is provided, scoped to that tenant only.

        Returns:
            Number of rows deleted.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        if tenant_id:
            cur = self._conn.execute(
                "DELETE FROM memories WHERE tenant_id=? AND created_at < ?",
                (tenant_id, cutoff),
            )
        else:
            cur = self._conn.execute(
                "DELETE FROM memories WHERE created_at < ?", (cutoff,)
            )
        self._conn.commit()
        return cur.rowcount

    def expire_ttl(self) -> int:
        """Purge memories whose expires_at timestamp has passed. Returns count deleted."""
        now_iso = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (now_iso,),
        )
        self._conn.commit()
        return cur.rowcount

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _row_to_memory(r: sqlite3.Row) -> Memory:
        return Memory(
            id=r["id"],
            tenant_id=r["tenant_id"],
            user_id=r["user_id"],
            kind=r["kind"],
            content=r["content"],
            metadata=json.loads(r["metadata"]),
            provenance=json.loads(r["provenance"]),
            created_at=r["created_at"],
            expires_at=r["expires_at"],
        )

    def close(self) -> None:
        self._conn.close()
