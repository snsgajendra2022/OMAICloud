"""Local lexical search (BM25-lite) — no external embeddings / no LLM."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


_TOKEN = re.compile(r"[a-z0-9][a-z0-9_\-]{1,}", re.IGNORECASE)


@dataclass(frozen=True)
class SearchHit:
    doc_id: str
    score: float
    snippet: str
    source: str = "local"


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "")]


class LocalSearchIndex:
    """In-memory BM25-lite keyword index — not an LLM ranker."""

    def __init__(self, *, k1: float = 1.5, b: float = 0.75) -> None:
        self._docs: dict[str, str] = {}
        self._sources: dict[str, str] = {}
        self._tf: dict[str, Counter[str]] = {}
        self._df: Counter[str] = Counter()
        self._dl: dict[str, int] = {}
        self._k1 = k1
        self._b = b

    def add(self, doc_id: str, text: str, *, source: str = "local") -> None:
        if doc_id in self._docs:
            self.remove(doc_id)
        toks = _tokens(text)
        self._docs[doc_id] = text
        self._sources[doc_id] = source
        self._tf[doc_id] = Counter(toks)
        self._dl[doc_id] = max(1, len(toks))
        for term in set(toks):
            self._df[term] += 1

    def remove(self, doc_id: str) -> None:
        if doc_id not in self._docs:
            return
        for term in set(self._tf[doc_id]):
            self._df[term] -= 1
            if self._df[term] <= 0:
                del self._df[term]
        del self._docs[doc_id]
        del self._sources[doc_id]
        del self._tf[doc_id]
        del self._dl[doc_id]

    @property
    def size(self) -> int:
        return len(self._docs)

    def _avgdl(self) -> float:
        if not self._dl:
            return 1.0
        return sum(self._dl.values()) / len(self._dl)

    def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        q_terms = _tokens(query)
        if not q_terms or not self._docs:
            return []
        n = len(self._docs)
        avgdl = self._avgdl()
        scores: dict[str, float] = {}
        for doc_id, tf in self._tf.items():
            score = 0.0
            dl = self._dl[doc_id]
            for term in q_terms:
                if term not in tf:
                    continue
                df = self._df.get(term, 0)
                idf = math.log(1.0 + (n - df + 0.5) / (df + 0.5))
                f = tf[term]
                denom = f + self._k1 * (1.0 - self._b + self._b * dl / avgdl)
                score += idf * (f * (self._k1 + 1.0)) / denom
            if score > 0:
                scores[doc_id] = score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        hits: list[SearchHit] = []
        for doc_id, score in ranked:
            text = self._docs[doc_id]
            snippet = text[:280].replace("\n", " ").strip()
            hits.append(
                SearchHit(
                    doc_id=doc_id,
                    score=round(score, 4),
                    snippet=snippet,
                    source=self._sources.get(doc_id, "local"),
                )
            )
        return hits


def index_text_files(
    root: str | Path,
    *,
    index: LocalSearchIndex | None = None,
    patterns: tuple[str, ...] = ("*.md", "*.txt", "*.rst"),
    max_files: int = 200,
    max_chars: int = 8000,
) -> LocalSearchIndex:
    """Load local docs into a lexical index."""
    idx = index or LocalSearchIndex()
    root_path = Path(root)
    if not root_path.is_dir():
        return idx
    count = 0
    for pattern in patterns:
        for path in sorted(root_path.rglob(pattern)):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
            except OSError:
                continue
            if not text.strip():
                continue
            rel = str(path.relative_to(root_path))
            idx.add(rel, text, source=f"local:{root_path.name}")
            count += 1
            if count >= max_files:
                return idx
    return idx
