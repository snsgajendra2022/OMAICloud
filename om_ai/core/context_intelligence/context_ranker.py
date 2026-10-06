"""
OM Context Ranker.
"""

from __future__ import annotations

from .context_pack import ContextPack


class ContextRanker:

    def rank(
        self,
        pack: ContextPack,
    ) -> ContextPack:

        pack.documents.sort(
            key=lambda document: (
                document.score()
            ),
            reverse=True,
        )

        return pack

    def limit(
        self,
        pack: ContextPack,
        max_documents: int = 10,
    ) -> ContextPack:

        pack.documents = (
            pack.documents[
                :max_documents
            ]
        )

        return pack