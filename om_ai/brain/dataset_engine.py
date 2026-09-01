"""Dataset-powered brain — retrieve real answers from ingested corpora (no dummy templates).

Indexes instruction→output pairs from OM knowledge brain / genesis / chat SFT
into a local SQLite TF-IDF store used when the tiny model fails quality checks.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

DEFAULT_QA_DB = "artifacts/brain_qa.sqlite3"
DEFAULT_TENANT = "default"

_CORPUS_CANDIDATES = [
    "data/om-knowledge-brain-v1/train/om_knowledge_instruct_v1.jsonl",
    "data/omai-genesis-v1/train/omai_genesis_instruct_v1.jsonl",
    "data/om-chat-sft-v4-complete.jsonl",
    "data/continuous/sft_replay.jsonl",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]{2,}", (text or "").lower())


def _qa_db_path() -> Path:
    raw = os.environ.get("OM_BRAIN_QA_DB") or DEFAULT_QA_DB
    p = Path(raw)
    if not p.is_absolute():
        p = _repo_root() / p
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_qa_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS qa_pairs (
          id TEXT PRIMARY KEY,
          source TEXT,
          domain TEXT,
          question TEXT NOT NULL,
          answer TEXT NOT NULL,
          q_tokens TEXT,
          created_at REAL
        );
        CREATE TABLE IF NOT EXISTS qa_meta (
          key TEXT PRIMARY KEY,
          value TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_qa_domain ON qa_pairs(domain);
        """
    )
    conn.commit()
    return conn


def _pair_id(source: str, question: str, answer: str) -> str:
    h = hashlib.sha256(f"{source}\n{question}\n{answer[:400]}".encode()).hexdigest()
    return h[:24]


def _extract_pairs(obj: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Return (question, answer, domain) tuples from one JSONL object."""
    domain = str(obj.get("domain") or obj.get("skill") or obj.get("tag") or "")
    out: list[tuple[str, str, str]] = []

    instruction = str(obj.get("instruction") or obj.get("prompt") or obj.get("input") or "").strip()
    answer = str(obj.get("output") or obj.get("response") or obj.get("completion") or "").strip()
    if instruction and answer:
        out.append((instruction, answer, domain))

    msgs = obj.get("messages")
    if isinstance(msgs, list) and msgs:
        user = ""
        asst = ""
        for m in msgs:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "")
            content = str(m.get("content") or "").strip()
            if role == "user":
                user = content
            elif role == "assistant":
                asst = content
        if user and asst:
            out.append((user, asst, domain))
    return out


def iter_jsonl_pairs(path: Path, *, limit: int | None = None, stride: int = 1) -> Iterable[tuple[str, str, str, str]]:
    """Yield (source, question, answer, domain)."""
    if not path.is_file():
        return
    n = 0
    kept = 0
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            n += 1
            if stride > 1 and (n % stride) != 0:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if not isinstance(obj, dict):
                continue
            for q, a, domain in _extract_pairs(obj):
                if len(q) < 8 or len(a) < 20:
                    continue
                yield (path.name, q[:2000], a[:6000], domain[:80])
                kept += 1
                if limit is not None and kept >= limit:
                    return


def power_from_datasets(
    *,
    limit_per_file: int = 8000,
    stride: int = 5,
    also_rag: bool = True,
    rag_limit: int = 2500,
) -> dict[str, Any]:
    """Ingest powerful local corpora into QA brain (+ optional RAG KB)."""
    root = _repo_root()
    conn = _connect()
    inserted = 0
    scanned = 0
    sources: list[dict[str, Any]] = []
    t0 = time.time()

    for rel in _CORPUS_CANDIDATES:
        path = root / rel
        if not path.is_file():
            sources.append({"path": rel, "status": "missing"})
            continue
        file_ins = 0
        for source, q, a, domain in iter_jsonl_pairs(path, limit=limit_per_file, stride=stride):
            scanned += 1
            pid = _pair_id(source, q, a)
            toks = " ".join(_tokenize(q)[:80])
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO qa_pairs
                       (id, source, domain, question, answer, q_tokens, created_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (pid, source, domain, q, a, toks, time.time()),
                )
                if conn.total_changes:
                    file_ins += 1
                    inserted += 1
            except Exception:
                continue
        conn.commit()
        sources.append(
            {
                "path": rel,
                "status": "ok",
                "bytes": path.stat().st_size,
                "inserted": file_ins,
            }
        )

    total = conn.execute("SELECT COUNT(*) AS c FROM qa_pairs").fetchone()["c"]
    conn.execute(
        "INSERT OR REPLACE INTO qa_meta(key,value) VALUES (?,?)",
        ("last_power_at", str(time.time())),
    )
    conn.execute(
        "INSERT OR REPLACE INTO qa_meta(key,value) VALUES (?,?)",
        ("pair_count", str(total)),
    )
    conn.commit()

    rag_info: dict[str, Any] = {"enabled": also_rag, "ingested": 0}
    if also_rag:
        rag_info = _ingest_sample_into_rag(conn, limit=rag_limit)

    conn.close()
    return {
        "ok": True,
        "engine": "om-dataset-brain-v1",
        "qa_db": str(_qa_db_path()),
        "pairs_total": total,
        "pairs_inserted_this_run": inserted,
        "lines_scanned": scanned,
        "sources": sources,
        "rag": rag_info,
        "elapsed_sec": round(time.time() - t0, 2),
        "next": [
            "Restart om-ai serve",
            "Chat will retrieve real dataset answers when the tiny model fails",
            "Train larger weights (1B/7B) on the same corpora for generative leap",
        ],
        "honesty": (
            "This wires your real datasets into memory/retrieval. "
            "Human-surpassing generative intelligence still needs larger trained weights "
            "and more licensed data — architecture + corpora are now connected to chat."
        ),
    }


def _kb_path() -> str:
    raw = os.environ.get("OM_AI_KB") or "artifacts/knowledge.sqlite3"
    p = Path(raw)
    if not p.is_absolute():
        p = _repo_root() / p
    return str(p)


def _ingest_sample_into_rag(conn: sqlite3.Connection, *, limit: int = 2500) -> dict[str, Any]:
    try:
        from om_ai.knowledge.rag import PersistentKnowledgeBase
    except Exception as exc:
        return {"enabled": True, "error": str(exc), "ingested": 0}

    kb = PersistentKnowledgeBase(_kb_path(), chunk_size=900, overlap=80)
    tenant = os.environ.get("OM_AI_TENANT") or DEFAULT_TENANT
    rows = conn.execute(
        "SELECT id, question, answer, domain, source FROM qa_pairs ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    n = 0
    for r in rows:
        text = (
            f"Question: {r['question']}\n\n"
            f"Answer:\n{r['answer']}\n\n"
            f"Domain: {r['domain'] or 'general'} | Source: {r['source']}"
        )
        try:
            kb.ingest_text(
                text,
                tenant,
                doc_id=f"brain-qa-{r['id']}",
                metadata={"source": r["source"], "domain": r["domain"], "kind": "dataset_qa"},
                filename=f"{r['source']}:{r['id']}.txt",
                extension=".txt",
            )
            n += 1
        except Exception:
            continue
    return {"enabled": True, "kb": _kb_path(), "ingested": n, "tenant": tenant}


def status() -> dict[str, Any]:
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) AS c FROM qa_pairs").fetchone()["c"]
    by_src = [
        dict(r)
        for r in conn.execute(
            "SELECT source, COUNT(*) AS c FROM qa_pairs GROUP BY source ORDER BY c DESC"
        ).fetchall()
    ]
    meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM qa_meta").fetchall()}
    conn.close()
    return {
        "qa_db": str(_qa_db_path()),
        "pairs": total,
        "by_source": by_src,
        "meta": meta,
        "static_templates": os.environ.get("OM_STATIC_TEMPLATES", "0"),
    }


def retrieve_answer(query: str, *, k: int = 5, min_score: float = 0.18) -> dict[str, Any] | None:
    """Return best dataset-grounded answer for a user query."""
    q = (query or "").strip()
    if not q:
        return None
    q_tokens = _tokenize(q)
    if not q_tokens:
        return None
    # Distinctive tokens (drop ultra-common chat glue)
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "your", "what", "how",
        "who", "when", "where", "why", "are", "is", "was", "were", "can", "you",
        "please", "help", "about", "into", "have", "has", "will", "just", "like",
        "need", "want", "make", "tell", "explain", "define", "teach",
    }
    rare = [t for t in q_tokens if len(t) >= 4 and t not in stop][:14]
    if not rare:
        rare = [t for t in q_tokens if t not in stop][:10] or q_tokens[:8]

    conn = _connect()
    total = conn.execute("SELECT COUNT(*) AS c FROM qa_pairs").fetchone()["c"]
    if total <= 0:
        conn.close()
        return None

    clauses = " OR ".join(
        ["(q_tokens LIKE ? OR question LIKE ? OR answer LIKE ?)" for _ in rare]
    )
    params: list[str] = []
    for t in rare:
        params.extend([f"%{t}%", f"%{t}%", f"%{t}%"])
    rows = conn.execute(
        f"SELECT id, source, domain, question, answer, q_tokens FROM qa_pairs WHERE {clauses} LIMIT 1500",
        params,
    ).fetchall()
    conn.close()
    if not rows:
        return None

    q_set = Counter(q_tokens)
    q_norm = math.sqrt(sum(v * v for v in q_set.values())) or 1.0
    scored: list[tuple[float, Any]] = []
    rare_set = set(rare)
    for r in rows:
        t_tokens = _tokenize(r["question"]) + _tokenize(str(r["answer"])[:500])
        if not t_tokens:
            continue
        t_set = Counter(t_tokens)
        shared_rare = rare_set & set(t_tokens)
        if not shared_rare:
            continue
        # Score primarily on question similarity; answer overlap is secondary
        q_only = _tokenize(r["question"])
        q_only_set = Counter(q_only) if q_only else Counter()
        q_only_norm = math.sqrt(sum(v * v for v in q_only_set.values())) or 1.0
        dot_q = sum(q_set[t] * q_only_set[t] for t in q_set if t in q_only_set)
        score = (dot_q / (q_norm * q_only_norm)) if q_only else 0.0
        score += 0.14 * len(shared_rare)
        a_tok = set(_tokenize(r["answer"])[:80])
        score += 0.05 * len(rare_set & a_tok)
        # Prefer physics/science domains slightly for science queries
        dom = (r["domain"] or "").lower()
        if any(x in rare_set for x in ("electricity", "electric", "thermo", "physics", "energy")):
            if dom in {"physics", "science", "engineering", "history"}:
                score += 0.05
        if score >= min_score:
            scored.append((score, r))

    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]
    answer = str(best["answer"] or "").strip()
    if not answer:
        return None

    header = (
        f"**OM dataset brain** (matched `{best['domain'] or 'general'}` · "
        f"score {best_score:.2f} · source `{best['source']}`)\n\n"
    )
    body = answer
    extras = []
    for sc, row in scored[1:k]:
        if sc < best_score * 0.75:
            break
        snippet = " ".join(str(row["answer"] or "").strip().splitlines()[:3])[:220]
        if snippet:
            extras.append(f"- ({sc:.2f}) {snippet}")
    if extras:
        body += "\n\n### Related knowledge\n" + "\n".join(extras[:3])

    return {
        "answer": header + body,
        "score": best_score,
        "source": best["source"],
        "domain": best["domain"],
        "question": best["question"],
        "id": best["id"],
        "candidates": len(scored),
    }


def grounded_or_none(query: str) -> str | None:
    hit = retrieve_answer(query)
    if not hit:
        return None
    return str(hit["answer"])
