"""Friend mind — what a close friend would notice, say, or gently ask."""
from __future__ import annotations

import re
from typing import Any


class FriendMind:
    """
    After meaning + emotion + memory, decide the human stance:
    acknowledge, support, continue a thread, or ask one natural question
    (only when something real is missing — never canned FAQ).
    """

    def think(
        self,
        message: str,
        *,
        meaning: dict[str, Any] | None = None,
        emotion: dict[str, Any] | None = None,
        memory: dict[str, Any] | None = None,
        relationship: dict[str, Any] | None = None,
        topic: str = "general",
        locale: str = "en",
    ) -> dict[str, Any]:
        meaning = meaning or {}
        emotion = emotion or {}
        memory = memory or {}
        relationship = relationship or {}
        low = (message or "").lower().strip()
        label = str(emotion.get("label") or emotion.get("emotion") or "neutral")
        profile = memory.get("profile") or {}
        name = str(profile.get("name") or "").strip()
        addr = str(relationship.get("address") or ("Sir" if locale != "hi" else "Sir"))

        stance = "continue"
        friend_move = "acknowledge_and_help"
        ask: str | None = None
        hint_parts: list[str] = []

        # Situation reads — meta "talk like a human" beats generic affect labels
        if re.search(
            r"(insaan|human|natural|robot|machine|chatbot|\bbot\b|"
            r"baat\s+nahi|baat\s+nahin|tarah\s+baat|normal\s+baat|jaise\s+insaan)",
            low,
        ):
            stance = "own_it"
            friend_move = "be_more_human"
            hint_parts.append(
                "A friend would own the robotic vibe, promise natural talk, and invite the next beat."
            )
        elif re.search(r"\b(google|search|khoj|browser)\b|search\s+karo", low):
            open_it = bool(
                re.search(
                    r"\b(go|open|kholo|khol|launch|navigate|redirect|take\s+me)\b",
                    low,
                )
            )
            mq = re.search(
                r"(?:google(?:\s+search)?|search(?:\s+for)?|khoj)\s+(.+)$",
                low,
            )
            topic_q = (mq.group(1).strip(" .") if mq else "").strip()
            if open_it:
                stance = "act"
                friend_move = "commit_then_do"
                if locale == "hi":
                    hint_parts.append(
                        f"Bhai mode: Google khol do{(' — ' + topic_q) if topic_q else ''}. Short and warm."
                    )
                else:
                    hint_parts.append(
                        f"Brother mode: open Google{(' for ' + topic_q) if topic_q else ''}. Short and warm."
                    )
            else:
                stance = "research"
                friend_move = "search_then_explain"
                if locale == "hi":
                    hint_parts.append(
                        "Bhai mode: search karo lekin browser mat kholo. "
                        "Jo mila woh natural language me batao — kya mila, kya solution chahiye. "
                        "Sirf jab user 'go'/'open' bole tab browser kholo."
                    )
                else:
                    hint_parts.append(
                        "Brother mode: search but do NOT open the browser. "
                        "Tell what you found and what solution is needed, like a caring human. "
                        "Open Google only if they say go/open."
                    )
        elif label in {"frustration", "stress", "urgency", "sad"}:
            stance = "support"
            friend_move = "validate_then_one_step"
            hint_parts.append(
                "A friend would first acknowledge how they feel, then offer one concrete next step."
            )
        elif label in {"happy", "excitement"}:
            stance = "share"
            friend_move = "match_energy"
            hint_parts.append("A friend would match the energy briefly, then stay useful.")
        elif re.search(r"\b(continue|us[ei]|wahi|pehle|keep going)\b", low) or meaning.get("is_followup"):
            stance = "continue"
            friend_move = "pick_up_thread"
            if topic and topic != "general":
                hint_parts.append(
                    f"A friend would continue the earlier thread about {topic.replace('_', ' ')} without restarting."
                )
            else:
                hint_parts.append("A friend would pick up exactly where you left off.")
        elif meaning.get("requires_clarification") or (
            len(low.split()) <= 3 and not re.search(r"(?i)\b(hi|hello|hey|thanks|ok|haan|theek)\b", low)
        ):
            stance = "clarify"
            friend_move = "one_gentle_question"
            if not topic or topic == "general":
                ask = (
                    "Kis cheez pe kaam karna hai?"
                    if locale == "hi"
                    else "What are we working on?"
                )
                hint_parts.append(
                    "A friend would ask one short clarifying question — not an FAQ list."
                )
        else:
            hint_parts.append(
                "A friend would answer directly in natural spoken language, then stop."
            )

        if name:
            hint_parts.append(f"You know them as {name}.")
        hint_parts.append(f"Address naturally as {addr} when it fits.")
        hint_parts.append("Never sound like a helpdesk. Never say 'How can I help you'.")

        return {
            "stance": stance,
            "friend_move": friend_move,
            "optional_ask": ask,
            "system_hint": " ".join(hint_parts),
            "address": addr,
            "topic": topic,
            "emotion": label,
        }
