from __future__ import annotations

from .research_state import ResearchSource


class CitationManager:

    def build(
        self,
        sources: list[ResearchSource],
    ) -> list[dict[str, str]]:

        citations = []

        for index, source in enumerate(
            sources,
            start=1,
        ):

            citations.append(
                {
                    "id":
                        str(index),

                    "title":
                        source.title,

                    "url":
                        source.url,
                }
            )

        return citations