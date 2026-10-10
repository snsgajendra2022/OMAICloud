"""
OM Context Fusion.

Combines memory, RAG, research and conversation
into one reasoning context.
"""

from __future__ import annotations

from typing import Any

from .context_pack import ContextPack
from .context_ranker import ContextRanker


class ContextFusion:

    def __init__(
        self,
        ranker: ContextRanker | None = None,
    ) -> None:

        self.ranker = (
            ranker
            or ContextRanker()
        )

    def fuse(
        self,
        pack: ContextPack,
        *,
        max_documents: int = 10,
    ) -> ContextPack:

        pack = self.ranker.rank(
            pack
        )

        pack = self.ranker.limit(
            pack,
            max_documents,
        )

        pack.metadata[
            "document_count"
        ] = len(
            pack.documents
        )

        pack.metadata[
            "source_types"
        ] = sorted(
            {
                document.source_type
                for document in pack.documents
            }
        )

        pack.metadata[
            "top_score"
        ] = (
            pack.documents[0].score()
            if pack.documents
            else 0.0
        )

        return pack

    def to_reasoning_context(
        self,
        pack: ContextPack,
    ) -> dict[str, Any]:

        return {
            "query": pack.query,
            "language": pack.language,
            "intent": pack.intent,
            "domain": pack.domain,
            "emotion": pack.emotion,
            "topic": pack.topic,

            "knowledge": pack.evidence_text(),

            "documents": [
                document.to_dict()
                for document in pack.documents
            ],

            "memory": pack.memory,

            "research": pack.research,

            "context_metadata": pack.metadata,
        }