"""
OM RAG Engine.

Main Retrieval-Augmented Generation intelligence layer.

Flow:

User message
    ↓
Retrieve
    ↓
Rank
    ↓
Filter
    ↓
Build evidence
    ↓
Return RAG context
"""

from __future__ import annotations

from typing import Any

from .rag_context import RAGContext
from .rag_prompt import RAGPromptBuilder
from .rag_ranker import RAGRanker
from .rag_retriever import RAGRetriever
from .rag_quality import RAGQualityGate
class RAGEngine:

    VERSION = "1.0.0"

    def __init__(
        self,
        retriever: RAGRetriever | None = None,
        ranker: RAGRanker | None = None,
        prompt_builder: RAGPromptBuilder | None = None,
    ) -> None:

        self.retriever = (
            retriever
            or RAGRetriever()
        )

        self.ranker = (
            ranker
            or RAGRanker()
        )

        self.prompt_builder = (
            prompt_builder
            or RAGPromptBuilder()
        )
        self.quality_gate = RAGQualityGate()

    def retrieve(
        self,
        query: str,
        *,
        intent: str | None = None,
        domain: str | None = None,
        language: str | None = None,
        dataset_type: str | None = None,
        limit: int = 5,
        min_similarity: float = 0.30,
        minimum_relevance: float = 0.30,
    ) -> RAGContext:

        context = self.retriever.retrieve(
            query,
            intent=intent,
            domain=domain,
            language=language,
            dataset_type=dataset_type,
            limit=limit,
            min_similarity=min_similarity,
        )

        context = self.ranker.rank(
            context
        )

        context = self.ranker.filter(
            context,
            minimum_relevance=minimum_relevance,
        )

        return context

    def build_evidence(
        self,
        context: RAGContext,
    ) -> str:

        return self.prompt_builder.build(
            context
        )

    def run(
        self,
        query: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        context = self.retrieve(
            query,
            **kwargs,
        )

        evidence = self.build_evidence(
            context
        )
        quality = self.quality_gate.evaluate(
            context
        )
        return {
            "version": self.VERSION,
            "query": query,
            "retrieved": context.retrieved,
            "confidence": context.confidence,
            "source_count": context.source_count,
            "quality": quality,
            "context": context,
            "evidence": evidence if quality["usable"] else "",
        }