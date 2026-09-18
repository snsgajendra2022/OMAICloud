"""Rank memory hits for retrieval context."""
from __future__ import annotations

import re
from typing import Any


class MemoryRanker:
    """Lightweight lexical + recency ranking (no large keyword dicts)."""

    def __init__(self) -> None:
        self._token = re.compile(r"[a-z0-9_]{2,}", re.I)

    def _tokens(self, text: str) -> set[str]:
        return {t.lower() for t in self._token.findall(text or "")}

    def score_row(
        self,
        row: dict[str, Any],
        query: str,
        *,
        index_from_end: int = 0,
    ) -> float:
        qtok = self._tokens(query)
        content = str(row.get("content") or "")
        key = str(row.get("key") or "")
        tags = " ".join(str(t) for t in (row.get("tags") or []))
        ctok = self._tokens(content + " " + key + " " + tags)
        overlap = len(qtok & ctok)
        base = overlap * 2.0
        kind = str(row.get("kind") or "")
        if kind == "preference":
            base += 0.5
        if kind == "semantic":
            base += 1.0
        recency = max(0.0, 1.5 - index_from_end * 0.05)
        conf = float((row.get("meta") or {}).get("confidence") or 0.0)
        return base + recency + conf * 0.3

    def rank(
        self,
        rows: list[dict[str, Any]],
        query: str,
        *,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        if not rows:
            return []
        scored: list[tuple[float, dict[str, Any]]] = []
        n = len(rows)
        for i, row in enumerate(rows):
            idx = n - 1 - i
            scored.append((self.score_row(row, query, index_from_end=idx), row))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[dict[str, Any]] = []
        for sc, row in scored[:limit]:
            item = dict(row)
            item["_rank_score"] = round(sc, 3)
            out.append(item)
        return out
