"""Exact-hash deduplication."""
from __future__ import annotations

import hashlib
from typing import Any, Iterable


def content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def dedupe_rows(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    removed = 0
    for row in rows:
        text = str(row.get("text") or "")
        h = str(row.get("content_hash") or content_hash(text))
        row = {**row, "content_hash": h}
        if h in seen:
            removed += 1
            continue
        seen.add(h)
        out.append(row)
    return out, removed
