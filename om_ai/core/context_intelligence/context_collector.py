"""
OM Context Collector.

Collects information from existing OM intelligence systems
without making those systems responsible for final response generation.
"""

from __future__ import annotations

from typing import Any

from .context_document import ContextDocument
from .context_pack import ContextPack


class ContextCollector:

    def collect(
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
    ) -> ContextPack:

        pack = ContextPack(
            query=message,
            language=language,
            intent=intent,
            domain=domain,
            emotion=emotion,
            topic=topic,
        )

        self._add_rag(
            pack,
            rag,
        )

        self._add_memory(
            pack,
            memory,
        )

        self._add_research(
            pack,
            research,
        )

        self._add_conversation(
            pack,
            conversation_context,
        )

        return pack

    # =========================================================
    # RAG
    # =========================================================

    def _add_rag(
        self,
        pack: ContextPack,
        rag: dict[str, Any] | None,
    ) -> None:

        if not rag:
            return

        context = rag.get(
            "context"
        )

        if context is None:
            return

        documents = getattr(
            context,
            "documents",
            [],
        )

        for document in documents:

            content = (
                getattr(
                    document,
                    "ideal_response",
                    "",
                )
                or getattr(
                    document,
                    "input_text",
                    "",
                )
            )

            if not content:
                continue

            pack.documents.append(
                ContextDocument(
                    content=str(
                        content
                    ),
                    source_type="rag",
                    source_id=str(
                        getattr(
                            document,
                            "item_id",
                            "",
                        )
                    ),
                    relevance=float(
                        getattr(
                            document,
                            "similarity",
                            0.0,
                        )
                    ),
                    confidence=float(
                        getattr(
                            context,
                            "confidence",
                            0.0,
                        )
                    ),
                    importance=float(
                        getattr(
                            document,
                            "quality_score",
                            0.0,
                        )
                    ),
                    trust=0.80,
                    metadata={
                        "domain": getattr(
                            document,
                            "domain",
                            "",
                        ),
                        "intent": getattr(
                            document,
                            "intent",
                            "",
                        ),
                    },
                )
            )

    # =========================================================
    # MEMORY
    # =========================================================

    def _add_memory(
        self,
        pack: ContextPack,
        memory: Any,
    ) -> None:

        if not memory:
            return

        if isinstance(
            memory,
            dict,
        ):

            items = [
                memory
            ]

        elif isinstance(
            memory,
            list,
        ):

            items = memory

        else:

            items = []

        for item in items:

            if not isinstance(
                item,
                dict,
            ):

                continue

            pack.memory.append(
                item
            )

            content = (
                item.get("content")
                or item.get("text")
                or item.get("value")
            )

            if not content:
                continue

            pack.documents.append(
                ContextDocument(
                    content=str(
                        content
                    ),
                    source_type="memory",
                    source_id=str(
                        item.get(
                            "id",
                            "",
                        )
                    ),
                    relevance=float(
                        item.get(
                            "relevance",
                            0.5,
                        )
                    ),
                    confidence=float(
                        item.get(
                            "confidence",
                            0.8,
                        )
                    ),
                    importance=float(
                        item.get(
                            "importance",
                            0.7,
                        )
                    ),
                    trust=0.90,
                    metadata=item,
                )
            )

    # =========================================================
    # RESEARCH
    # =========================================================

    def _add_research(
        self,
        pack: ContextPack,
        research: Any,
    ) -> None:

        if not research:
            return

        if isinstance(
            research,
            dict,
        ):

            items = [
                research
            ]

        elif isinstance(
            research,
            list,
        ):

            items = research

        else:

            items = []

        for item in items:

            if not isinstance(
                item,
                dict,
            ):

                continue

            pack.research.append(
                item
            )

            content = (
                item.get("content")
                or item.get("summary")
                or item.get("text")
                or item.get("answer")
            )

            if not content:
                continue

            pack.documents.append(
                ContextDocument(
                    content=str(
                        content
                    ),
                    source_type="research",
                    source_id=str(
                        item.get(
                            "id",
                            item.get(
                                "url",
                                "",
                            ),
                        )
                    ),
                    relevance=float(
                        item.get(
                            "relevance",
                            0.7,
                        )
                    ),
                    confidence=float(
                        item.get(
                            "confidence",
                            0.7,
                        )
                    ),
                    importance=0.8,
                    trust=float(
                        item.get(
                            "trust",
                            0.75,
                        )
                    ),
                    metadata=item,
                )
            )

    # =========================================================
    # CONVERSATION
    # =========================================================

    def _add_conversation(
        self,
        pack: ContextPack,
        context: dict[str, Any] | None,
    ) -> None:

        if not context:
            return

        pack.metadata[
            "conversation_context"
        ] = context

        previous = (
            context.get(
                "previous_messages"
            )
            or context.get(
                "conversation"
            )
        )

        if not previous:
            return

        if not isinstance(
            previous,
            list,
        ):

            return

        for item in previous[
            -5:
        ]:

            if isinstance(
                item,
                str,
            ):

                content = item

            elif isinstance(
                item,
                dict,
            ):

                content = (
                    item.get(
                        "content"
                    )
                    or item.get(
                        "message"
                    )
                    or ""
                )

            else:

                continue

            if not content:
                continue

            pack.documents.append(
                ContextDocument(
                    content=str(
                        content
                    ),
                    source_type="conversation",
                    relevance=0.70,
                    confidence=0.90,
                    importance=0.60,
                    recency=1.0,
                    trust=0.95,
                )
            )