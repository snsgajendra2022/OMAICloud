from __future__ import annotations

from typing import Any

from .citation_manager import CitationManager
from .content_extractor import ContentExtractor
from .fact_verifier import FactVerifier
from .page_reader import PageReader
from .research_state import (
    ResearchSource,
    ResearchState,
)
from .search_agent import SearchAgent
from .source_ranker import SourceRanker
from .web_connector import WebConnector


class ResearchEngine:
    """Full research path: query → search → rank → verify → citations."""

    def __init__(
        self,
        *,
        connector: WebConnector | None = None,
    ) -> None:
        self.search_agent = SearchAgent()
        self.connector = connector or WebConnector()
        self.reader = PageReader()
        self.extractor = ContentExtractor()
        self.ranker = SourceRanker()
        self.verifier = FactVerifier()
        self.citations = CitationManager()

    def research(
        self,
        question: str,
        *,
        understanding: dict[str, Any] | None = None,
        max_queries: int = 3,
        results_per_query: int = 5,
        max_sources: int = 8,
    ) -> ResearchState:
        state = ResearchState(
            query=question,
            status="researching",
        )

        state.search_queries = self.search_agent.create_queries(
            question,
            understanding,
            max_queries=max_queries,
        )

        seen_urls: set[str] = set()

        for query in state.search_queries:
            results = self.connector.search(
                query,
                limit=results_per_query,
            )
            state.search_results.extend(results)

            for result in results:
                url = (result.url or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                content = ""
                content_type = ""
                from_snippet = False
                page = self.reader.read(url)
                if page is not None and page.status_code < 400:
                    content_type = page.content_type or ""
                    content = self.extractor.extract(page.text) or ""

                # Fallback: use search snippet so research is never empty
                # when search succeeded but page fetch failed.
                if not content:
                    content = (result.snippet or "").strip()
                    from_snippet = bool(content)

                if not content:
                    continue

                source = ResearchSource(
                    title=result.title or url,
                    url=url,
                    content=content,
                    metadata={
                        "search_source": result.source,
                        "content_type": content_type,
                        "from_snippet": from_snippet,
                    },
                )
                source = self.ranker.rank(source, query=question)
                state.sources.append(source)

        state.sources.sort(
            key=lambda item: item.final_score,
            reverse=True,
        )
        state.sources = state.sources[:max_sources]
        state.verified_facts = self.verifier.verify(state.sources)
        state.citations = self.citations.build(state.sources)
        state.summary_context = self._build_context(state)

        if state.sources:
            state.confidence = sum(
                source.final_score for source in state.sources
            ) / len(state.sources)
            state.status = "complete"
        else:
            state.confidence = 0.0
            state.status = "no_sources"

        return state

    @staticmethod
    def _build_context(state: ResearchState) -> str:
        sections = []
        for index, source in enumerate(state.sources, start=1):
            sections.append(
                "\n".join(
                    [
                        f"[SOURCE {index}]",
                        f"Title: {source.title}",
                        f"URL: {source.url}",
                        f"Confidence: {source.final_score:.2f}",
                        "",
                        source.content[:5000],
                    ]
                )
            )
        return "\n\n".join(sections)
