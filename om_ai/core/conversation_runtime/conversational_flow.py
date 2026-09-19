"""OM conversational flow — topic continuity without canned follow-ups.

Tracks what the user is talking about so the runtime can stay coherent.
Does not invent or append static “Sir, should I…” lines onto answers.
The brain owns the spoken reply.
"""
from __future__ import annotations

import re
from typing import Any


class ConversationalFlow:
    def __init__(self) -> None:
        self.topic_memory: dict[str, str] = {}
        self._last_follow: dict[str, str] = {}
        self.topic_patterns: dict[str, tuple[str, ...]] = {
            "model_pipeline": (
                "model",
                "llm",
                "training",
                "train",
                "checkpoint",
                "weights",
                "dataset",
                "fine tune",
                "inference",
            ),
            "voice_system": (
                "voice",
                "tts",
                "speech",
                "microphone",
                "audio",
                "hearing",
                "listen",
            ),
            "avatar_system": (
                "avatar",
                "3d",
                "animation",
                "face",
                "lip sync",
                "character",
            ),
            "memory_system": (
                "memory",
                "remember",
                "preference",
                "history",
                "context",
            ),
            "om_project": (
                "om",
                "companion",
                "assistant",
                "jarvis",
                "ai system",
            ),
            "debugging": (
                "bug",
                "error",
                "exception",
                "failed",
                "fix",
                "issue",
            ),
            "planning": (
                "plan",
                "roadmap",
                "architecture",
                "design",
                "build",
            ),
        }

    def infer_topic(self, text: str) -> str:
        blob = (text or "").lower()
        scores: dict[str, int] = {}
        for topic, keywords in self.topic_patterns.items():
            score = sum(1 for word in keywords if word in blob)
            if score:
                scores[topic] = score
        if not scores:
            return "general"
        return max(scores, key=scores.get)

    def update_context(self, session_id: str, text: str) -> str:
        topic = self.infer_topic(text)
        if session_id:
            self.topic_memory[session_id] = topic
        return topic

    def current_topic(self, session_id: str) -> str:
        return self.topic_memory.get(session_id, "general")

    def should_follow_up(
        self,
        answer: str,
        user_text: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Never auto-append. Brain already speaks. Metadata-only path stays off."""
        del answer, user_text, context
        return False

    def follow_up(
        self,
        user_text: str,
        answer: str,
        *,
        topic: str = "",
        session_id: str = "",
    ) -> str | None:
        """Production voice path: do not inject internal follow-up copy."""
        del user_text, answer, topic, session_id
        return None

    def merge_follow_up(self, answer: str, follow: str | None) -> str:
        """Keep the brain answer intact — never concatenate canned lines."""
        del follow
        return (answer or "").strip()

    def already_asks(self, answer: str) -> bool:
        text = (answer or "").strip()
        if not text:
            return False
        if "?" in text or "؟" in text:
            return True
        return bool(re.search(r"(kya|kia|batao|boliye)\b", text.lower()))
