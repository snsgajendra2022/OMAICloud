from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .research_state import SearchResult


class SearchProvider(ABC):

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[SearchResult]:
        raise NotImplementedError


class LiveKnowledgeSearchProvider(SearchProvider):
    """Default provider — uses OM live_knowledge web search (no API key)."""

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[SearchResult]:
        try:
            from om_ai.live_knowledge.web_search import search_web
        except Exception:
            return []

        out: list[SearchResult] = []
        try:
            hits = search_web(query, limit=limit) or []
        except Exception:
            return []

        for hit in hits:
            title = str(getattr(hit, "title", "") or "").strip()
            url = str(getattr(hit, "url", "") or "").strip()
            snippet = str(getattr(hit, "snippet", "") or "").strip()
            source = str(getattr(hit, "source", "") or "web").strip()
            if not url:
                continue
            out.append(
                SearchResult(
                    title=title or url,
                    url=url,
                    snippet=snippet,
                    source=source,
                )
            )
            if len(out) >= limit:
                break
        return out


class WebConnector:

    def __init__(
        self,
        provider: SearchProvider | None = None,
    ) -> None:
        # Always have a working default so ResearchEngine is not a stub.
        self.provider: SearchProvider = provider or LiveKnowledgeSearchProvider()

    def set_provider(
        self,
        provider: SearchProvider,
    ) -> None:
        self.provider = provider

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[SearchResult]:
        if self.provider is None:
            return []
        try:
            return self.provider.search(query, limit=limit) or []
        except Exception:
            return []
