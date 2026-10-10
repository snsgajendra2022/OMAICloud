"""
OM Unified Context Intelligence Engine.
"""

from __future__ import annotations

from typing import Any

from .context_collector import ContextCollector
from .context_fusion import ContextFusion
from .context_pack import ContextPack


class ContextIntelligenceEngine:

    VERSION = "1.0.0"

    def __init__(
        self,
        collector: ContextCollector | None = None,
        fusion: ContextFusion | None = None,
    ) -> None:

        self.collector = (
            collector
            or ContextCollector()
        )

        self.fusion = (
            fusion
            or ContextFusion()
        )

    def build(
        self,
        message: str,
        *,
        language: str = "en",
        intent: str = "",
        domain: str = "",
        emotion: str = "",
        topic: str = "",
        rag: dict[str, Any] | None = None,
        memory: Any = None,
        research: Any = None,
        conversation_context: dict[str, Any] | None = None,
        max_documents: int = 10,
    ) -> ContextPack:

        pack = self.collector.collect(
            message,
            language=language,
            intent=intent,
            domain=domain,
            emotion=emotion,
            topic=topic,
            rag=rag,
            memory=memory,
            research=research,
            conversation_context=conversation_context,
        )

        return self.fusion.fuse(
            pack,
            max_documents=max_documents,
        )

    def build_reasoning_context(
        self,
        message: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        pack = self.build(
            message,
            **kwargs,
        )

        return self.fusion.to_reasoning_context(
            pack
        )

    def inspect(
        self,
        message: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        pack = self.build(
            message,
            **kwargs,
        )

        return {
            "version": self.VERSION,
            "query": pack.query,
            "document_count": len(
                pack.documents
            ),
            "sources": pack.metadata.get(
                "source_types",
                [],
            ),
            "top_score": pack.metadata.get(
                "top_score",
                0.0,
            ),
            "context": pack.to_dict(),
        }