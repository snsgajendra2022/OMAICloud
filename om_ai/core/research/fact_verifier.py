from __future__ import annotations

from collections import defaultdict
from typing import Any

from .research_state import ResearchSource


class FactVerifier:

    def verify(
        self,
        sources: list[ResearchSource],
    ) -> list[dict[str, Any]]:

        if not sources:
            return []

        # For now this builds verified evidence groups.
        # Later OM's reasoning model should extract
        # propositions and perform claim-level verification.

        evidence = []

        for source in sources:

            if source.final_score < 0.50:
                continue

            evidence.append(
                {
                    "source":
                        source.url,

                    "title":
                        source.title,

                    "confidence":
                        source.final_score,

                    "content":
                        source.content[
                            :3000
                        ],
                }
            )

        return evidence