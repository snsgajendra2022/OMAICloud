"""Dialogue policy from semantic frame."""
from __future__ import annotations

from typing import Any


class DialoguePolicy:
    def decide(self, semantic: dict[str, Any]) -> dict[str, Any]:
        mode = semantic.get("conversation_mode") or "assist"
        intent = semantic.get("intent") or "chat"
        if mode == "social":
            return {
                "allow_brief_reply": True,
                "prefer_runtime_fast_path": True,
                "max_questions": 0,
                "policy": "social_first",
            }
        if mode == "clarify":
            return {
                "allow_brief_reply": False,
                "prefer_runtime_fast_path": False,
                "max_questions": 1,
                "policy": "ask_one_question",
            }
        if mode == "task":
            return {
                "allow_brief_reply": False,
                "prefer_runtime_fast_path": False,
                "max_questions": 1 if semantic.get("requires_clarification") else 0,
                "policy": "task_focused",
            }
        if intent == "followup" or mode == "continue":
            return {
                "allow_brief_reply": False,
                "prefer_runtime_fast_path": False,
                "max_questions": 0,
                "policy": "thread_continuity",
            }
        return {
            "allow_brief_reply": True,
            "prefer_runtime_fast_path": semantic.get("confidence", 0) > 0.85,
            "max_questions": 0,
            "policy": "balanced_assist",
        }
