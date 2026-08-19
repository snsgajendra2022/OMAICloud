"""Configured live knowledge sources (URLs / local docs). Not LLM providers."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class KnowledgeSource:
    name: str
    kind: str  # url | local | rss | template
    locator: str
    enabled: bool = True


DEFAULT_SOURCES: list[KnowledgeSource] = [
    KnowledgeSource("om_docs", "local", "docs/", enabled=True),
]

# Query patterns → concrete URLs (official pages, not LLM calls).
_URL_HINTS: list[tuple[re.Pattern[str], list[str]]] = [
    (
        re.compile(r"\bionic\b.*(release|version|changelog)|latest\s+ionic", re.I),
        [
            "https://github.com/ionic-team/ionic-framework/releases",
            "https://ionicframework.com/docs",
        ],
    ),
    (
        re.compile(r"\b(python)\b.*(release|version)|latest\s+python", re.I),
        ["https://www.python.org/downloads/"],
    ),
    (
        re.compile(r"\b(node\.?js|nodejs)\b.*(release|version)|latest\s+node", re.I),
        ["https://nodejs.org/en/download"],
    ),
    (
        re.compile(r"prime\s+minister\s+of\s+nepal|nepal.*prime\s+minister", re.I),
        [
            "https://en.wikipedia.org/wiki/List_of_prime_ministers_of_Nepal",
            "https://en.wikipedia.org/wiki/Prime_Minister_of_Nepal",
        ],
    ),
]


def resolve_repo_root() -> Path:
    env = (os.getenv("OM_AI_ROOT") or "").strip()
    if env:
        return Path(env).resolve()
    # om_ai/live_knowledge/sources.py → repo root
    return Path(__file__).resolve().parents[2]


def configured_sources() -> list[KnowledgeSource]:
    """Merge defaults with ``OM_LIVE_KNOWLEDGE_SOURCES`` (comma-separated paths/URLs)."""
    sources = list(DEFAULT_SOURCES)
    extra = (os.getenv("OM_LIVE_KNOWLEDGE_SOURCES") or "").strip()
    if not extra:
        return sources
    for i, part in enumerate(extra.split(",")):
        part = part.strip()
        if not part:
            continue
        if part.startswith("http://") or part.startswith("https://"):
            sources.append(KnowledgeSource(f"env_url_{i}", "url", part, True))
        else:
            sources.append(KnowledgeSource(f"env_local_{i}", "local", part, True))
    return sources


def urls_for_query(query: str) -> list[str]:
    """Map known time-sensitive topics to official/reference URLs."""
    urls: list[str] = []
    for pattern, targets in _URL_HINTS:
        if pattern.search(query or ""):
            urls.extend(targets)
    # Explicit URLs in the query
    for token in (query or "").split():
        if token.startswith("http://") or token.startswith("https://"):
            urls.append(token.rstrip(".,);]"))
    # Dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def local_roots(sources: Iterable[KnowledgeSource] | None = None) -> list[Path]:
    root = resolve_repo_root()
    paths: list[Path] = []
    for src in sources or configured_sources():
        if not src.enabled or src.kind != "local":
            continue
        p = Path(src.locator)
        if not p.is_absolute():
            p = root / p
        if p.is_dir():
            paths.append(p)
    return paths
