"""Decide follow-ups and topic shifts."""
from __future__ import annotations

import re
from typing import Any


class ConversationalFlow:
    def infer_topic(self, text: str) -> str:
        low = (text or "").lower()
        if re.search(r"(?i)\b(model|pipeline|train|checkpoint)\b", low):
            return "model_pipeline"
        if re.search(r"(?i)\b(voice|tts|speech|mic)\b", low):
            return "voice_system"
        if re.search(r"(?i)\b(project|om|companion)\b", low):
            return "om_project"
        if re.search(r"(?i)\b(bug|error|fix|debug)\b", low):
            return "debugging"
        return "general"

    def follow_up(self, user_text: str, answer: str, *, topic: str = "") -> str | None:
        # Encourage continuous dialogue — one short question if answer lacks one
        if "?" in (answer or ""):
            return None
        t = topic or self.infer_topic(user_text)
        hints = {
            "model_pipeline": "Shall I inspect the model pipeline next?",
            "voice_system": "Want me to tune the voice further?",
            "debugging": "Should I dig into the error next?",
            "om_project": "What part of the project should we open first?",
            "general": "What would you like to do next, Sir?",
        }
        return hints.get(t, hints["general"])

    def merge_follow_up(self, answer: str, follow: str | None) -> str:
        if not follow:
            return answer
        a = (answer or "").rstrip()
        if not a:
            return follow
        return f"{a} {follow}"
