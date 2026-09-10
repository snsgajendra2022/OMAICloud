from __future__ import annotations


class FormatSelector:

    def select(
        self,
        *,
        intent: str,
        message: str,
    ) -> str:

        if intent in {
            "coding",
            "software_creation",
            "implementation",
        }:
            return "code_first"

        if intent in {
            "planning",
            "architecture",
        }:
            return "structured"

        if intent in {
            "casual_conversation",
            "conversation",
            "greeting",
        }:
            return "natural"

        return "direct"