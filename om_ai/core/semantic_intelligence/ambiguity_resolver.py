"""Ambiguity resolver — detect unclear asks and propose one natural clarify."""
from __future__ import annotations

import re
from typing import Any


class AmbiguityResolver:
    def resolve(
        self,
        text: str,
        *,
        intent: str = "conversation",
        speech_act: str = "statement",
        locale: str = "en",
    ) -> dict[str, Any]:
        low = (text or "").lower().strip()
        tokens = low.split()

        ambiguous = False
        reason = ""
        ask = None

        if len(tokens) <= 1 and low not in {"hi", "hello", "hey", "ok", "okay", "haan", "thanks", "stop"}:
            ambiguous = True
            reason = "too_short"
            ask = "Kis cheez pe kaam karna hai?" if locale == "hi" else "What are we working on?"
        elif re.search(r"(?i)\b(this|that|it)\b", low) and len(tokens) <= 3 and intent in {
            "action",
            "question",
            "problem",
        }:
            ambiguous = True
            reason = "unclear_referent"
            ask = "Kaunsa wala?" if locale == "hi" else "Which one do you mean?"
        elif intent == "action" and not re.search(
            r"(?i)\b(open|kholo|launch|delete|send|run|start)\s+\S+", low
        ):
            ambiguous = True
            reason = "missing_target"
            ask = "Kya open/run karna hai?" if locale == "hi" else "What should I open or run?"
        elif intent == "research" and len(tokens) <= 2:
            ambiguous = True
            reason = "missing_query"
            ask = "Kya search karun?" if locale == "hi" else "What should I search for?"

        # Sharing / greeting — never force clarification
        if intent in {"sharing", "greeting", "thanks", "joke"}:
            ambiguous = False
            ask = None
            reason = ""

        return {
            "ambiguous": ambiguous,
            "reason": reason,
            "clarify_ask": ask,
            "needs_clarification": ambiguous,
        }
