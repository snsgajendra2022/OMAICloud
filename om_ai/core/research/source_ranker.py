from __future__ import annotations

from urllib.parse import urlparse

from .research_state import ResearchSource


class SourceRanker:

    HIGH_AUTHORITY_DOMAINS = {
        "github.com": 0.85,
        "docs.python.org": 0.95,
        "developer.mozilla.org": 0.95,
        "react.dev": 0.98,
        "w3.org": 0.98,
        "ietf.org": 0.98,
    }

    def rank(
        self,
        source: ResearchSource,
        *,
        query: str,
    ) -> ResearchSource:

        source.authority_score = (
            self._authority(
                source.url
            )
        )

        source.relevance_score = (
            self._relevance(
                query,
                source.content,
            )
        )

        source.freshness_score = (
            self._freshness(
                source
            )
        )

        source.final_score = (
            source.authority_score
            * 0.40
            +
            source.relevance_score
            * 0.45
            +
            source.freshness_score
            * 0.15
        )

        return source

    def _authority(
        self,
        url: str,
    ) -> float:

        domain = (
            urlparse(url)
            .netloc
            .lower()
            .removeprefix("www.")
        )

        if domain in (
            self.HIGH_AUTHORITY_DOMAINS
        ):
            return (
                self.HIGH_AUTHORITY_DOMAINS[
                    domain
                ]
            )

        if domain.endswith(".gov"):
            return 0.95

        if domain.endswith(".edu"):
            return 0.85

        return 0.55

    @staticmethod
    def _relevance(
        query: str,
        content: str,
    ) -> float:

        query_words = {
            word.lower()
            for word in query.split()
            if len(word) > 2
        }

        content_lower = (
            content.lower()
        )

        if not query_words:
            return 0.0

        matches = sum(
            1
            for word in query_words
            if word in content_lower
        )

        return min(
            matches
            / len(query_words),
            1.0,
        )

    @staticmethod
    def _freshness(
        source: ResearchSource,
    ) -> float:

        value = source.metadata.get(
            "freshness"
        )

        if isinstance(
            value,
            (float, int),
        ):
            return max(
                0.0,
                min(float(value), 1.0),
            )

        return 0.5