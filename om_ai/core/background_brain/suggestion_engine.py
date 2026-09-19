from __future__ import annotations
from typing import Any

class SuggestionEngine:
    def morning(self, *, last_focus: str = "") -> str:
        focus = last_focus or "the companion voice pipeline"
        return f"Good morning, Sir. Yesterday you were on {focus}. Shall we continue?"

    def from_context(self, topic: str = "") -> str | None:
        if not topic:
            return None
        return f"Shall I stay on {topic.replace('_', ' ')}, Sir?"
