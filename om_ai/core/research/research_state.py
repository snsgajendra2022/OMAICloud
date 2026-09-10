from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    score: float = 0.0


@dataclass
class ResearchSource:
    title: str
    url: str
    content: str = ""
    source_type: str = "web"
    authority_score: float = 0.0
    relevance_score: float = 0.0
    freshness_score: float = 0.0
    final_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchState:
    query: str

    search_queries: list[str] = field(default_factory=list)

    search_results: list[SearchResult] = field(default_factory=list)

    sources: list[ResearchSource] = field(default_factory=list)

    verified_facts: list[dict[str, Any]] = field(default_factory=list)

    citations: list[dict[str, str]] = field(default_factory=list)

    summary_context: str = ""

    confidence: float = 0.0

    status: str = "created"

    errors: list[str] = field(default_factory=list)