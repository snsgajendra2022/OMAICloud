"""Digital neural simulation — adaptive memory graph (safe bio-inspired layer)."""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import time
from pathlib import Path
from typing import Any

_DB = Path("artifacts/neural_memory_graph.sqlite3")


def _conn() -> sqlite3.Connection:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(_DB), check_same_thread=False)
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS nodes (
          id TEXT PRIMARY KEY,
          label TEXT,
          weight REAL,
          hits INTEGER,
          updated_at REAL
        );
        CREATE TABLE IF NOT EXISTS edges (
          src TEXT,
          dst TEXT,
          weight REAL,
          PRIMARY KEY (src, dst)
        );
        """
    )
    c.commit()
    return c


def _nid(label: str) -> str:
    return hashlib.sha1(label.encode()).hexdigest()[:16]


def experience(tokens: list[str], *, boost: float = 1.0) -> dict[str, Any]:
    """Record co-occurring concepts; strengthen connections (Hebbian-style)."""
    labels = [t.strip().lower() for t in tokens if t and len(t.strip()) >= 3][:24]
    if len(labels) < 2:
        return {"ok": False, "reason": "need_2_plus_tokens"}
    c = _conn()
    now = time.time()
    ids = []
    for lab in labels:
        nid = _nid(lab)
        ids.append(nid)
        row = c.execute("SELECT weight, hits FROM nodes WHERE id=?", (nid,)).fetchone()
        if row:
            c.execute(
                "UPDATE nodes SET weight=?, hits=?, updated_at=?, label=? WHERE id=?",
                (float(row[0]) + 0.1 * boost, int(row[1]) + 1, now, lab, nid),
            )
        else:
            c.execute(
                "INSERT INTO nodes(id,label,weight,hits,updated_at) VALUES (?,?,?,?,?)",
                (nid, lab, 1.0 * boost, 1, now),
            )
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            row = c.execute("SELECT weight FROM edges WHERE src=? AND dst=?", (a, b)).fetchone()
            w = (float(row[0]) + 0.05 * boost) if row else 0.2 * boost
            c.execute(
                "INSERT OR REPLACE INTO edges(src,dst,weight) VALUES (?,?,?)",
                (a, b, w),
            )
            c.execute(
                "INSERT OR REPLACE INTO edges(src,dst,weight) VALUES (?,?,?)",
                (b, a, w),
            )
    c.commit()
    n = c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    e = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    c.close()
    return {"ok": True, "nodes": n, "edges": e, "learned": labels[:8]}


def activate(query: str, *, k: int = 6) -> list[dict[str, Any]]:
    toks = [t for t in query.lower().replace(",", " ").split() if len(t) >= 3][:12]
    if not toks:
        return []
    c = _conn()
    scored: dict[str, float] = {}
    for t in toks:
        nid = _nid(t)
        for row in c.execute(
            "SELECT dst, weight FROM edges WHERE src=? ORDER BY weight DESC LIMIT ?",
            (nid, k),
        ):
            scored[row[0]] = scored.get(row[0], 0.0) + float(row[1])
    out = []
    for nid, w in sorted(scored.items(), key=lambda x: -x[1])[:k]:
        lab = c.execute("SELECT label, weight, hits FROM nodes WHERE id=?", (nid,)).fetchone()
        if lab:
            out.append({"label": lab[0], "edge_weight": w, "node_weight": lab[1], "hits": lab[2]})
    c.close()
    return out


def status() -> dict[str, Any]:
    c = _conn()
    n = c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    e = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    c.close()
    return {
        "layer": "digital_neural_simulation",
        "nodes": n,
        "edges": e,
        "db": str(_DB),
        "note": "Safe digital equivalent of bio-inspired learning — not biological microbes.",
    }
