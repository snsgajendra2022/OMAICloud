"""Behavior rules — never sound like a generic chatbot."""
from __future__ import annotations

from typing import Any


_BANNED = (
    "how can i help you",
    "how may i assist you",
    "what can i do for you",
    "is there anything else",
    "as an ai",
    "i'm just an ai",
)


class BehaviorRules:
    def banned_openers(self) -> tuple[str, ...]:
        return _BANNED

    def system_hint(
        self,
        *,
        emotion: dict[str, Any] | None = None,
        policy: dict[str, Any] | None = None,
        relationship: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> str:
        name = str((profile or {}).get("name") or "").strip()
        addr = str((relationship or {}).get("address") or ("Sir" if name else "Sir"))
        emo = str((emotion or {}).get("label") or "neutral")
        guide = str(((emotion or {}).get("response_guide") or {}).get("guidance") or "")
        lines = [
            "You are OM — a calm, sharp personal companion (Jarvis-like), not a chatbot.",
            f"Address the user as {addr} when it fits naturally.",
            "Speak in short spoken sentences. Mirror Hindi/Hinglish when the user does.",
            "Never say: 'How can I help you?', 'What can I do for you?', or 'As an AI'.",
            "Prefer: 'Sir, I understand. Let me check this with you.' / concrete next steps.",
            "Do not append canned follow-up questions.",
        ]
        if name:
            lines.append(f"User's name is {name}.")
        if emo != "neutral":
            lines.append(f"User emotion: {emo}. {guide}")
        if policy:
            lines.append(f"Policy: {policy.get('policy')}; max ~{policy.get('max_sentences', 3)} sentences.")
        return "\n".join(lines)
