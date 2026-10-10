"""
OM Unified Context Pack.

Everything the reasoning layer needs for one user turn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .context_document import ContextDocument


@dataclass(slots=True)
class ContextPack:

    query: str

    language: str = "en"

    intent: str = ""

    domain: str = ""

    emotion: str = ""

    topic: str = ""

    documents: list[ContextDocument] = field(
        default_factory=list
    )

    memory: list[dict[str, Any]] = field(
        default_factory=list
    )

    research: list[dict[str, Any]] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def ranked_documents(
        self,
    ) -> list[ContextDocument]:

        return sorted(
            self.documents,
            key=lambda item: item.score(),
            reverse=True,
        )

    def top_documents(
        self,
        limit: int = 8,
    ) -> list[ContextDocument]:

        return self.ranked_documents()[
            :limit
        ]

    def evidence_text(
        self,
        limit: int = 8,
    ) -> str:

        documents = self.top_documents(
            limit
        )

        if not documents:

            return ""

        sections: list[str] = []

        for index, document in enumerate(
            documents,
            start=1,
        ):

            sections.append(
                f"[Context {index} | "
                f"{document.source_type} | "
                f"score={document.score():.3f}]"
            )

            sections.append(
                document.content
            )

        return "\n\n".join(
            sections
        )

    def to_dict(self) -> dict[str, Any]:

        return {
            "query": self.query,
            "language": self.language,
            "intent": self.intent,
            "domain": self.domain,
            "emotion": self.emotion,
            "topic": self.topic,
            "documents": [
                item.to_dict()
                for item in self.documents
            ],
            "memory": self.memory,
            "research": self.research,
            "metadata": self.metadata,
        }