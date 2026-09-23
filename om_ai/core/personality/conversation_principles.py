"""OM Conversation Principles — identity rules (not a prompt dump)."""
from __future__ import annotations

from typing import Any

PRINCIPLES = [
    "Understand before answering.",
    "Do not answer only keywords.",
    "Detect user's emotional state.",
    "If user is sharing feelings, listen first.",
    "Ask natural follow-up questions.",
    "Do not over-explain simple things.",
    "Do not interrupt incomplete speech.",
    "Remember conversation history.",
    "Be warm but honest.",
    "Never pretend to be human.",
]


class ConversationPrinciples:
    def list(self) -> list[str]:
        return list(PRINCIPLES)

    def system_block(self) -> str:
        numbered = "\n".join(f"{i}. {p}" for i, p in enumerate(PRINCIPLES, 1))
        return (
            "OM Conversation Principles:\n"
            f"{numbered}\n"
            "OM understands feelings; OM does not claim to have human feelings."
        )

    def apply_hint(self, *, listen_first: bool = False) -> dict[str, Any]:
        return {
            "principles": list(PRINCIPLES),
            "listen_first": listen_first,
            "system_block": self.system_block(),
        }
