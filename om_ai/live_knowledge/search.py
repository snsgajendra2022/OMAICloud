"""Local lexical search stub (BM25-style placeholder; no external embeddings)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchHit:
    doc_id: str
    score: float
    snippet: str
    source: str = "local_stub"


class LocalSearchIndex:
    """In-memory keyword index stub — not an LLM ranker."""

    def __init__(self) -> None:
        self._docs: dict[str, str] = {}

    def add(self, doc_id: str, text: str, *, source: str = "local") -> None:
        self._docs[doc_id] = text

    def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        q = (query or "").lower().strip()
        if not q:
            return []
        terms = [t for t in q.split() if t]
        hits: list[SearchHit] = []
        for doc_id, text in self._docs.items():
            lower = text.lower()
            score = sum(1.0 for t in terms if t in lower)
            if score <= 0:
                continue
            snippet = text[:280].replace("\n", " ")
            hits.append(SearchHit(doc_id=doc_id, score=score, snippet=snippet, source="local_stub"))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]
