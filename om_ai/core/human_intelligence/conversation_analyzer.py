"""Conversation analyzer — surface structure of the turn."""
from __future__ import annotations

import re
from typing import Any


class ConversationAnalyzer:
    def analyze(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        text = (message or "").strip()
        low = text.lower()
        hist = history or []
        words = low.split()
        unfinished = bool(re.search(r"\.\.\.\s*$|,\s*$|\bbut\s*$|\band\s*$|\bto\s*$", text))
        question = "?" in text or bool(
            re.match(r"(?i)^(what|why|how|when|where|who|kya|kaise|kab|kyun)\b", low)
        )
        venting = bool(
            re.search(
                r"(?i)\b(today was|rough day|hard day|difficult|exhausted|"
                r"can't|cannot|won't work|everything|nothing works)\b",
                low,
            )
        )
        celebration = bool(
            re.search(r"(?i)\b(fixed|done|shipped|finally|solved|worked|passed)\b", low)
        )
        return {
            "length": len(words),
            "unfinished": unfinished,
            "is_question": question,
            "venting": venting,
            "celebration": celebration,
            "history_turns": len(hist),
            "short_turn": len(words) <= 4,
            "ack_only": bool(re.fullmatch(r"(?i)(ok|okay|haan|theek|ji|yes|no|nahi)\.?", low)),
        }
