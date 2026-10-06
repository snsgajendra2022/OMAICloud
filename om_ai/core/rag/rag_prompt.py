"""
OM RAG Prompt Context Builder.

Builds structured evidence for the reasoning layer.
"""

from __future__ import annotations

from .rag_context import RAGContext


class RAGPromptBuilder:

    def build(
        self,
        context: RAGContext,
    ) -> str:

        if not context.has_knowledge:

            return (
                "No relevant internal dataset knowledge "
                "was retrieved."
            )

        sections: list[str] = []

        sections.append(
            "OM INTERNAL KNOWLEDGE"
        )

        sections.append(
            "Use the following retrieved examples "
            "as supporting evidence."
        )

        sections.append(
            "Do not blindly copy them. "
            "Reason over them and adapt the answer "
            "to the user's actual request."
        )

        for index, document in enumerate(
            context.documents,
            start=1,
        ):

            sections.append(
                f"\n--- Knowledge {index} ---"
            )

            sections.append(
                f"Similarity: "
                f"{document.similarity:.4f}"
            )

            sections.append(
                f"Quality: "
                f"{document.quality_score:.4f}"
            )

            if document.domain:

                sections.append(
                    f"Domain: {document.domain}"
                )

            if document.intent:

                sections.append(
                    f"Intent: {document.intent}"
                )

            if document.meaning:

                sections.append(
                    f"Meaning: {document.meaning}"
                )

            if document.reasoning_summary:

                sections.append(
                    "Reasoning guidance: "
                    f"{document.reasoning_summary}"
                )

            if document.verification_strategy:

                sections.append(
                    "Verification: "
                    f"{document.verification_strategy}"
                )

            sections.append(
                f"Example request: "
                f"{document.input_text}"
            )

            sections.append(
                f"Example response: "
                f"{document.ideal_response}"
            )

        return "\n".join(
            sections
        )