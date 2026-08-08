"""
Production RAG (Retrieval-Augmented Generation) engine with persistent SQLite index.

Embedding backend: hashed TF-IDF bag-of-words over numpy — no external AI API required.

Production swap note:
    Subclass PersistentKnowledgeBase and override embed_text(text, tenant_id) -> np.ndarray
    to plug in any dense encoder (sentence-transformers, OpenAI /v1/embeddings, Cohere, etc.).
    The embedding dimension is stored per-tenant; the rest of the pipeline is unchanged.

Supported document formats:
    .txt, .md / .markdown, .json, .csv, .html / .htm — stdlib parsers (always available)
    .pdf   — requires: pip install pypdf      (skipped with warning if missing)
    .docx  — requires: pip install python-docx (skipped with warning if missing)
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import math
import re
import sqlite3
import struct
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable

import numpy as np

logger = logging.getLogger(__name__)

# ─── Optional heavy parsers ───────────────────────────────────────────────────

try:
    import pypdf  # type: ignore[import]
    _HAS_PYPDF = True
except ImportError:
    _HAS_PYPDF = False

try:
    import docx as _docx  # python-docx  # type: ignore[import]
    _HAS_DOCX = True
except ImportError:
    _HAS_DOCX = False

# ─── Public data classes ──────────────────────────────────────────────────────


@dataclass
class KnowledgeDoc:
    """In-memory document (backward-compat with LocalKnowledgeBase)."""
    id: str
    text: str
    metadata: dict


@dataclass
class ChunkRecord:
    """A retrieved chunk with provenance."""
    chunk_id: str
    tenant_id: str
    doc_id: str
    text: str
    metadata: dict
    score: float = 0.0


# ─── HTML stripper ────────────────────────────────────────────────────────────


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _strip_html(html: str) -> str:
    s = _HTMLStripper()
    s.feed(html)
    return s.get_text()


# ─── Document parsers ─────────────────────────────────────────────────────────


def _parse_text(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


def _parse_json(content: bytes) -> str:
    try:
        return json.dumps(json.loads(content.decode("utf-8", errors="replace")), indent=2)
    except Exception:
        return content.decode("utf-8", errors="replace")


def _parse_csv(content: bytes) -> str:
    text = content.decode("utf-8", errors="replace")
    return "\n".join(",".join(row) for row in csv.reader(io.StringIO(text)))


def _parse_html(content: bytes) -> str:
    return _strip_html(content.decode("utf-8", errors="replace"))


def _parse_pdf(content: bytes) -> str:
    if not _HAS_PYPDF:
        raise ImportError(
            "pypdf is not installed. Install it with: pip install pypdf"
        )
    reader = pypdf.PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_docx(content: bytes) -> str:
    if not _HAS_DOCX:
        raise ImportError(
            "python-docx is not installed. Install it with: pip install python-docx"
        )
    doc = _docx.Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs)


_PARSERS: dict[str, Callable[[bytes], str]] = {
    ".txt": _parse_text,
    ".md": _parse_text,
    ".markdown": _parse_text,
    ".json": _parse_json,
    ".csv": _parse_csv,
    ".html": _parse_html,
    ".htm": _parse_html,
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
}


# ─── Overlap chunker ──────────────────────────────────────────────────────────


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """
    Split text into overlapping character-based chunks.

    Args:
        chunk_size: maximum characters per chunk (default 512).
        overlap: characters shared between consecutive chunks (default 64).

    Returns:
        List of non-empty chunk strings.
    """
    if not text.strip():
        return []
    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunk = text[start: start + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
        start += step
    return chunks


# ─── Hashed TF-IDF embeddings (no external API) ───────────────────────────────

DEFAULT_DIM = 512  # hash-space dimensionality; increase for denser representation
_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _term_freq(tokens: list[str]) -> dict[str, float]:
    c = Counter(tokens)
    total = max(1, sum(c.values()))
    return {t: n / total for t, n in c.items()}


def _vocab_slot(term: str, dim: int) -> int:
    """Deterministic, collision-tolerant slot assignment via MD5 digest."""
    return int(hashlib.md5(term.encode()).hexdigest(), 16) % dim


def build_tfidf_vector(
    text: str,
    idf: dict[str, float],
    dim: int = DEFAULT_DIM,
) -> np.ndarray:
    """
    Build a hashed TF-IDF vector.  Collisions are tolerated (additive accumulation).
    Production note: replace this with embed_text() override for dense embeddings.
    """
    tokens = _tokenize(text)
    tf = _term_freq(tokens)
    vec = np.zeros(dim, dtype=np.float32)
    for term, tf_val in tf.items():
        idf_val = idf.get(term, math.log(2.0) + 1.0)  # smoothed default IDF
        vec[_vocab_slot(term, dim)] += tf_val * idf_val
    norm = float(np.linalg.norm(vec))
    if norm > 0.0:
        vec /= norm
    return vec


def _pack_vec(vec: np.ndarray) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def _unpack_vec(blob: bytes) -> np.ndarray:
    n = len(blob) // 4
    return np.array(struct.unpack(f"{n}f", blob), dtype=np.float32)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a)) * float(np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom > 0.0 else 0.0


# ─── BM25 ─────────────────────────────────────────────────────────────────────


def _bm25(
    query_tokens: list[str],
    doc_tokens: list[str],
    df: dict[str, int],
    N: int,
    avgdl: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    dl = len(doc_tokens)
    tf_map = Counter(doc_tokens)
    score = 0.0
    for term in query_tokens:
        if term not in tf_map:
            continue
        tf_val = float(tf_map[term])
        n_t = df.get(term, 0)
        idf_val = math.log((N - n_t + 0.5) / (n_t + 0.5) + 1.0)
        score += idf_val * (tf_val * (k1 + 1.0)) / (
            tf_val + k1 * (1.0 - b + b * dl / max(1.0, avgdl))
        )
    return score


# ─── SQLite schema ────────────────────────────────────────────────────────────

_DDL = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS rag_documents (
    doc_id      TEXT    NOT NULL,
    tenant_id   TEXT    NOT NULL,
    filename    TEXT    NOT NULL DEFAULT '',
    extension   TEXT    NOT NULL DEFAULT '',
    metadata    TEXT    NOT NULL DEFAULT '{}',
    char_count  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL,
    PRIMARY KEY (tenant_id, doc_id)
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    chunk_id     TEXT    PRIMARY KEY,
    tenant_id    TEXT    NOT NULL,
    doc_id       TEXT    NOT NULL,
    text         TEXT    NOT NULL,
    embedding    BLOB,
    metadata     TEXT    NOT NULL DEFAULT '{}',
    content_hash TEXT    NOT NULL,
    token_count  INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_tenant  ON rag_chunks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc     ON rag_chunks(tenant_id, doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_hash    ON rag_chunks(content_hash);

CREATE TABLE IF NOT EXISTS rag_vocab (
    term       TEXT NOT NULL,
    tenant_id  TEXT NOT NULL,
    df         INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (tenant_id, term)
);
"""


# ─── PersistentKnowledgeBase ──────────────────────────────────────────────────


class PersistentKnowledgeBase:
    """
    Production RAG engine backed by SQLite with:
      - Multi-format document ingestion (txt, md, json, csv, html, pdf*, docx*)
      - Configurable overlap chunking
      - Hashed TF-IDF embeddings (numpy; no external API)
      - Hybrid semantic + BM25 retrieval
      - Lexical overlap reranker
      - Full tenant isolation (tenant_id scopes all reads/writes)
      - build_context() for prompt assembly
      - delete_document() for document lifecycle management

    *pdf requires pypdf; docx requires python-docx — both gracefully skipped if absent.
    """

    def __init__(
        self,
        db_path: str = "artifacts/om_ai_rag.sqlite3",
        chunk_size: int = 512,
        overlap: int = 64,
        embed_dim: int = DEFAULT_DIM,
        hybrid_alpha: float = 0.6,   # 0.0 = pure BM25, 1.0 = pure semantic
    ) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._embed_dim = embed_dim
        self._hybrid_alpha = hybrid_alpha

        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    # ── Embedding hook (override to swap in dense encoder) ───────────────────

    def embed_text(self, text: str, tenant_id: str = "default") -> np.ndarray:
        """
        Return a float32 numpy vector for text.
        Default: hashed TF-IDF (offline, no API).
        Override this method to use sentence-transformers, OpenAI, etc.
        """
        return build_tfidf_vector(text, self._load_idf(tenant_id), self._embed_dim)

    # ── IDF helpers ───────────────────────────────────────────────────────────

    def _load_idf(self, tenant_id: str) -> dict[str, float]:
        rows = self._conn.execute(
            "SELECT term, df FROM rag_vocab WHERE tenant_id=?", (tenant_id,)
        ).fetchall()
        N = max(1, self._doc_count(tenant_id))
        return {r["term"]: math.log((N + 1.0) / (r["df"] + 1.0)) + 1.0 for r in rows}

    def _doc_count(self, tenant_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM rag_documents WHERE tenant_id=?", (tenant_id,)
        ).fetchone()
        return int(row[0]) if row else 0

    def _update_vocab(self, tenant_id: str, chunks: list[str]) -> None:
        """Increment DF counts for each term appearing in the new chunks."""
        df: dict[str, int] = {}
        for chunk in chunks:
            for term in set(_tokenize(chunk)):
                df[term] = df.get(term, 0) + 1
        for term, count in df.items():
            self._conn.execute(
                """INSERT INTO rag_vocab(term, tenant_id, df) VALUES(?,?,?)
                   ON CONFLICT(tenant_id, term) DO UPDATE SET df = df + excluded.df""",
                (term, tenant_id, count),
            )

    # ── Parsing ───────────────────────────────────────────────────────────────

    @staticmethod
    def parse_content(content: bytes, extension: str) -> str:
        """
        Parse raw bytes to text using the extension-matched parser.
        Raises ValueError for unsupported extensions.
        Raises ImportError for pdf/docx when optional dependency is missing.
        """
        ext = extension if extension.startswith(".") else f".{extension}"
        ext = ext.lower()
        parser = _PARSERS.get(ext)
        if parser is None:
            supported = ", ".join(sorted(_PARSERS))
            raise ValueError(
                f"Unsupported extension {ext!r}. Supported: {supported}"
            )
        return parser(content)

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest_file(
        self,
        path: str | Path,
        tenant_id: str,
        doc_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """
        Ingest a file from disk into the knowledge base.

        Returns:
            doc_id assigned to the document.
        """
        p = Path(path)
        content = p.read_bytes()
        ext = p.suffix.lower() or ".txt"
        doc_id = doc_id or str(uuid.uuid4())
        meta = {"filename": p.name, **(metadata or {})}
        try:
            text = self.parse_content(content, ext)
        except ImportError as exc:
            logger.warning("Optional parser unavailable for %r: %s — storing error stub.", ext, exc)
            text = f"[parse unavailable for {p.name}: {exc}]"
        except Exception as exc:
            logger.error("Failed to parse %r: %s", p.name, exc)
            raise
        return self.ingest_text(
            text,
            tenant_id,
            doc_id=doc_id,
            metadata=meta,
            filename=p.name,
            extension=ext,
        )

    def ingest_text(
        self,
        text: str,
        tenant_id: str,
        doc_id: str | None = None,
        metadata: dict | None = None,
        filename: str = "",
        extension: str = ".txt",
    ) -> str:
        """
        Chunk, embed, and persist raw text for a tenant.

        Returns:
            doc_id assigned to the document.
        """
        doc_id = doc_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        meta = metadata or {}

        self._conn.execute(
            """INSERT OR REPLACE INTO rag_documents
               (doc_id, tenant_id, filename, extension, metadata, char_count, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (doc_id, tenant_id, filename, extension, json.dumps(meta), len(text), now),
        )
        # Remove any prior chunks for this document (re-ingest / update)
        self._conn.execute(
            "DELETE FROM rag_chunks WHERE tenant_id=? AND doc_id=?",
            (tenant_id, doc_id),
        )

        chunks = chunk_text(text, self._chunk_size, self._overlap)
        if not chunks:
            self._conn.commit()
            return doc_id

        self._update_vocab(tenant_id, chunks)
        self._conn.commit()

        idf = self._load_idf(tenant_id)
        for i, chunk_str in enumerate(chunks):
            chunk_id = f"{doc_id}::{i}"
            content_hash = hashlib.sha256(chunk_str.encode()).hexdigest()
            vec = build_tfidf_vector(chunk_str, idf, self._embed_dim)
            chunk_meta = {**meta, "chunk_index": i, "doc_id": doc_id}
            self._conn.execute(
                """INSERT OR REPLACE INTO rag_chunks
                   (chunk_id, tenant_id, doc_id, text, embedding, metadata,
                    content_hash, token_count, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    chunk_id, tenant_id, doc_id, chunk_str,
                    _pack_vec(vec), json.dumps(chunk_meta),
                    content_hash, len(_tokenize(chunk_str)), now,
                ),
            )
        self._conn.commit()
        logger.info(
            "Ingested doc_id=%s tenant=%s filename=%r chunks=%d",
            doc_id, tenant_id, filename, len(chunks),
        )
        return doc_id

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        tenant_id: str,
        k: int = 5,
        use_hybrid: bool = True,
        doc_id_filter: str | None = None,
    ) -> list[ChunkRecord]:
        """
        Retrieve top-k chunks for the query within tenant_id.
        Tenant isolation guaranteed: only chunks belonging to tenant_id are returned.

        Args:
            query: natural language search query.
            tenant_id: scope retrieval to this tenant only.
            k: number of results to return.
            use_hybrid: combine semantic (TF-IDF cosine) + BM25; set False for pure semantic.
            doc_id_filter: restrict to a specific document.
        """
        q_emb = self.embed_text(query, tenant_id)
        q_tokens = _tokenize(query)

        rows = self._conn.execute(
            "SELECT chunk_id, doc_id, text, embedding, metadata FROM rag_chunks WHERE tenant_id=?",
            (tenant_id,),
        ).fetchall()
        if not rows:
            return []

        # BM25 corpus statistics (tenant-scoped)
        N = self._doc_count(tenant_id)
        doc_lengths: dict[str, int] = {}
        for r in rows:
            doc_lengths[r["doc_id"]] = doc_lengths.get(r["doc_id"], 0) + len(_tokenize(r["text"]))
        avgdl = sum(doc_lengths.values()) / max(1, len(doc_lengths))
        df_rows = self._conn.execute(
            "SELECT term, df FROM rag_vocab WHERE tenant_id=?", (tenant_id,)
        ).fetchall()
        df_map = {r["term"]: r["df"] for r in df_rows}

        scored: list[tuple[float, sqlite3.Row]] = []
        for row in rows:
            if doc_id_filter and row["doc_id"] != doc_id_filter:
                continue

            # Semantic score
            sem = 0.0
            if row["embedding"]:
                doc_emb = _unpack_vec(bytes(row["embedding"]))
                sem = cosine_sim(q_emb, doc_emb)

            # Lexical BM25 score (normalised to [0,1])
            lex = 0.0
            if use_hybrid:
                raw = _bm25(q_tokens, _tokenize(row["text"]), df_map, N, avgdl)
                lex = raw / (raw + 10.0)

            final = self._hybrid_alpha * sem + (1.0 - self._hybrid_alpha) * lex
            scored.append((final, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        # Over-fetch for reranker
        candidates = scored[: k * 4]
        candidates = self._rerank(query, candidates)
        return [
            ChunkRecord(
                chunk_id=r["chunk_id"],
                tenant_id=tenant_id,
                doc_id=r["doc_id"],
                text=r["text"],
                metadata=json.loads(r["metadata"]),
                score=round(s, 5),
            )
            for s, r in candidates[:k]
        ]

    def _rerank(
        self,
        query: str,
        candidates: list[tuple[float, sqlite3.Row]],
    ) -> list[tuple[float, sqlite3.Row]]:
        """Lexical overlap reranker: boosts candidates sharing query terms."""
        q_words = set(_tokenize(query))
        if not q_words:
            return candidates
        reranked = []
        for score, row in candidates:
            doc_words = set(_tokenize(row["text"]))
            overlap = len(q_words & doc_words) / len(q_words)
            reranked.append((score + 0.1 * overlap, row))
        reranked.sort(key=lambda x: x[0], reverse=True)
        return reranked

    # ── Context builder ───────────────────────────────────────────────────────

    def build_context(
        self, query: str, tenant_id: str, k: int = 5
    ) -> dict[str, Any]:
        """
        Assemble a RAG context passage and citation list for prompt injection.

        Returns:
            {
                "context_text": str,   # numbered passages ready for prompt
                "citations": [
                    {
                        "index": int,
                        "doc_id": str,
                        "chunk_id": str,
                        "score": float,
                        "metadata": dict,
                    },
                    ...
                ]
            }
        """
        chunks = self.search(query, tenant_id, k=k)
        parts: list[str] = []
        citations: list[dict] = []
        for idx, c in enumerate(chunks, 1):
            parts.append(f"[{idx}] {c.text.strip()}")
            citations.append(
                {
                    "index": idx,
                    "doc_id": c.doc_id,
                    "chunk_id": c.chunk_id,
                    "score": c.score,
                    "metadata": c.metadata,
                }
            )
        return {"context_text": "\n\n".join(parts), "citations": citations}

    # ── Document management ───────────────────────────────────────────────────

    def delete_document(self, tenant_id: str, doc_id: str) -> int:
        """
        Delete a document and all its chunks for the given tenant.

        Returns:
            Number of chunks deleted.
        """
        cur = self._conn.execute(
            "DELETE FROM rag_chunks WHERE tenant_id=? AND doc_id=?",
            (tenant_id, doc_id),
        )
        self._conn.execute(
            "DELETE FROM rag_documents WHERE tenant_id=? AND doc_id=?",
            (tenant_id, doc_id),
        )
        self._conn.commit()
        logger.info("Deleted doc_id=%s tenant=%s (%d chunks)", doc_id, tenant_id, cur.rowcount)
        return cur.rowcount

    # ── Compatibility helpers (API / tools) ───────────────────────────────────

    def add(
        self,
        doc_id: str,
        text: str,
        metadata: dict | None = None,
        tenant_id: str = "default",
    ) -> str:
        """Backward-compatible ingest used by FastAPI and older callers."""
        return self.ingest_text(text, tenant_id=tenant_id, doc_id=doc_id, metadata=metadata)

    def search_compat(self, query: str, k: int = 5, tenant_id: str = "default") -> list[dict]:
        """Return dict results for tool/API callers that expect LocalKnowledgeBase shape."""
        chunks = self.search(query, tenant_id=tenant_id, k=k)
        return [
            {
                "score": c.score,
                "id": c.doc_id,
                "chunk_id": c.chunk_id,
                "text": c.text,
                "metadata": c.metadata,
                "tenant_id": c.tenant_id,
            }
            for c in chunks
        ]

    def list_documents(self, tenant_id: str) -> list[dict]:
        """List all document records for a tenant (no chunk text returned)."""
        rows = self._conn.execute(
            """SELECT doc_id, filename, extension, char_count, created_at, metadata
               FROM rag_documents WHERE tenant_id=? ORDER BY created_at DESC""",
            (tenant_id,),
        ).fetchall()
        return [
            {
                "doc_id": r["doc_id"],
                "filename": r["filename"],
                "extension": r["extension"],
                "char_count": r["char_count"],
                "created_at": r["created_at"],
                "metadata": json.loads(r["metadata"]),
            }
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()


# ─── Legacy in-memory LocalKnowledgeBase (backward compat) ───────────────────


class LocalKnowledgeBase:
    """
    Lightweight in-memory TF-IDF knowledge base (backward-compatible).
    Does NOT persist across process restarts and has NO tenant isolation.
    For production use, prefer PersistentKnowledgeBase.
    """

    def __init__(self) -> None:
        self.docs: list[KnowledgeDoc] = []
        self.df: Counter = Counter()

    @staticmethod
    def _terms(text: str) -> list[str]:
        return re.findall(r"[a-z0-9_]+", text.lower())

    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self.docs.append(KnowledgeDoc(doc_id, text, metadata or {}))
        self.df.update(set(self._terms(text)))

    def search(self, query: str, k: int = 5) -> list[dict]:
        q = self._terms(query)
        n = max(1, len(self.docs))
        scored = []
        for d in self.docs:
            tf = Counter(self._terms(d.text))
            score = 0.0
            for term in q:
                idf = math.log((n + 1) / (1 + self.df[term])) + 1
                score += (tf[term] / max(1, sum(tf.values()))) * idf
            if score > 0:
                scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"score": s, "id": d.id, "text": d.text, "metadata": d.metadata}
            for s, d in scored[:k]
        ]
