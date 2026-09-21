"""Conversation style hints for the generator (dynamic, not script banks)."""
from __future__ import annotations

from typing import Any


class ConversationStyle:
    def compose(
        self,
        *,
        intent: dict[str, Any] | None = None,
        empathy: dict[str, Any] | None = None,
        emotion: dict[str, Any] | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intent = intent or {}
        empathy = empathy or {}
        emotion = emotion or {}
        prefs = preferences or {}
        detail = str(prefs.get("detail_level") or prefs.get("answer_style") or "balanced")
        lines = [
            "Speak like a close intelligent companion — natural, warm, concise.",
            "Never use helpdesk / FAQ phrases.",
            f"Lead with {empathy.get('lead_with') or 'acknowledge'}; then {empathy.get('then') or 'help'}.",
            f"Response intent: {intent.get('intent') or 'answer'}.",
            f"Emotion: {emotion.get('emotion') or 'neutral'}; style: {emotion.get('response_style') or 'steady'}.",
            f"User detail preference: {detail}.",
        ]
        if intent.get("should_ask"):
            lines.append("End with one gentle question only if it deepens the moment.")
        if intent.get("should_act"):
            lines.append("Confirm the action in human words, then proceed.")
        return {
            "system_hint": " ".join(lines),
            "max_sentences": int(empathy.get("max_sentences") or 3),
            "detail_level": detail,
        }
