"""Communication style for friend personality."""
from __future__ import annotations

from typing import Any


class CommunicationStyle:
    banned = (
        "How can I help you",
        "What can I do for you",
        "Please complete your sentence",
        "As an AI",
        "Share one more detail",
    )

    def compose_hint(
        self,
        *,
        friendship: dict[str, Any] | None = None,
        locale: str = "en",
        address: str = "Sir",
    ) -> str:
        friendship = friendship or {}
        parts = [
            "OM personality: loyal Jarvis-like friend.",
            f"Address as {address} when it fits.",
            f"Style mode: {friendship.get('mode') or 'companion'}.",
            str(friendship.get("hint") or ""),
            "Never use helpdesk openers.",
        ]
        if locale == "hi":
            parts.append("Reply in warm Hinglish when the user speaks that way.")
        ex = str(friendship.get("example") or "").strip()
        if ex:
            parts.append(f"Tone example (do not copy verbatim unless it fits): {ex}")
        return " ".join(p for p in parts if p)
