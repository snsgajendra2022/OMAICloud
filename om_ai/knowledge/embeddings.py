"""Local hashed embeddings + metadata vector index (no cloud embed API)."""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import struct
import time
from pathlib import Path
from typing import Any

import numpy as np

from om_ai.knowledge.rag import DEFAULT_DIM, build_tfidf_vector, cosine_sim

_DDL = """
CREATE TABLE IF NOT EXISTS vectors (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding BLOB NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vectors_tenant ON vectors(tenant_id);
"""


def embed_text(text: str, *, dim: int = DEFAULT_DIM, idf: dict[str, float] | None = None) -> np.ndarray:
    """Deterministic local embedding (hashed TF-IDF / n-gram hash space)."""
    return build_tfidf_vector(text or "", idf or {}, dim)


def _pack(vec: np.ndarray) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def _unpack(blob: bytes) -> np.ndarray:
    n = len(blob) // 4
    return np.array(struct.unpack(f"{n}f", blob), dtype=np.float32)


class EmbeddingIndex:
    """SQLite vector store: ingest text+metadata, cosine search."""

    def __init__(self, db_path: str = "artifacts/om_embeddings.sqlite3", dim: int = DEFAULT_DIM) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.dim = dim
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    def upsert(
        self,
        text: str,
        *,
        tenant_id: str = "default",
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> str:
        body = (text or "").strip()
        vid = doc_id or hashlib.sha256(f"{tenant_id}:{body[:800]}".encode()).hexdigest()[:32]
        vec = embed_text(body, dim=self.dim)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO vectors (id, tenant_id, text, embedding, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                vid,
                tenant_id,
                body,
                _pack(vec),
                json.dumps(metadata or {}),
                time.time(),
            ),
        )
        self._conn.commit()
        return vid

    def search(
        self,
        query: str,
        *,
        tenant_id: str = "default",
        k: int = 5,
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        q = embed_text(query, dim=self.dim)
        rows = self._conn.execute(
            "SELECT id, text, embedding, metadata FROM vectors WHERE tenant_id=?",
            (tenant_id,),
        ).fetchall()
        scored: list[tuple[float, sqlite3.Row]] = []
        for row in rows:
            meta = json.loads(row["metadata"] or "{}")
            if domain and str(meta.get("domain") or "") not in {domain, ""}:
                if meta.get("domain") and meta.get("domain") != domain:
                    continue
            score = cosine_sim(q, _unpack(bytes(row["embedding"])))
            scored.append((score, row))
        scored.sort(key=lambda x: -x[0])
        out: list[dict[str, Any]] = []
        for score, row in scored[:k]:
            out.append(
                {
                    "id": row["id"],
                    "text": row["text"],
                    "score": round(float(score), 5),
                    "metadata": json.loads(row["metadata"] or "{}"),
                }
            )
        return out
