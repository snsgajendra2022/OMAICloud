"""
Context Intent Classifier — Tool Decision Layer front door.

Replaces naive: if "date" in message → use_date_tool

intent = classify(message)
  date_query     → date tool
  conversation   → normal chat (no tools)
  calculation    → calculator
  coding         → code tools
  research       → knowledge (internal only)
  general        → model / normal chat
"""
from __future__ import annotations

import re
from typing import Any


class ContextIntentClassifier:
    """Classify user message for tool decision — never keyword-substring alone."""

    DATE_QUERY = "date_query"
    CONVERSATION = "conversation"
    CALCULATION = "calculation"
    CODING = "coding"
    RESEARCH = "research"
    GENERAL = "general"

    def classify(self, text: str) -> str:
        return str(self.classify_detailed(text).get("intent") or self.GENERAL)

    def classify_detailed(self, text: str) -> dict[str, Any]:
        raw = (text or "").strip()
        t = re.sub(r"\bmoring\b", "morning", raw.lower())
        t = re.sub(r"\bafernoon\b", "afternoon", t)

        # 1) Social / greeting — never date tool
        if self._is_conversation(t):
            return {
                "intent": self.CONVERSATION,
                "use_tools": False,
                "tools": [],
                "reason": "social_or_greeting",
            }

        # 2) Explicit calendar ask
        if self._is_date_query(t):
            return {
                "intent": self.DATE_QUERY,
                "use_tools": True,
                "tools": ["date"],
                "reason": "calendar_request",
            }

        # 3) Calculation
        if re.search(r"\d+\s*%\s*of\s*\d+", t) or re.search(
            r"\b(calculate|compute|what is)\s+\d", t
        ):
            return {
                "intent": self.CALCULATION,
                "use_tools": True,
                "tools": ["calculator"],
                "reason": "math_request",
            }

        # 3b) Live / weather → web tool (when enabled)
        if re.search(r"\b(weather|forecast|temperature)\b", t):
            return {
                "intent": self.RESEARCH,
                "use_tools": True,
                "tools": ["web", "knowledge"],
                "reason": "live_weather",
            }

        # 4) Coding
        if re.search(
            r"\b(write|create|implement|debug|fastapi|react|python\s+code|function)\b",
            t,
        ):
            return {
                "intent": self.CODING,
                "use_tools": True,
                "tools": ["code_execution", "knowledge"],
                "reason": "coding_request",
            }

        # 5) Research-ish
        if re.search(r"\b(what is|explain|research|who is|tell me about)\b", t) and len(
            t.split()
        ) >= 3:
            return {
                "intent": self.RESEARCH,
                "use_tools": True,
                "tools": ["knowledge"],
                "reason": "research_with_knowledge",
                "internal_knowledge": True,
            }

        return {
            "intent": self.GENERAL,
            "use_tools": False,
            "tools": [],
            "reason": "general_chat",
        }

    def _is_conversation(self, t: str) -> bool:
        if re.search(
            r"\bhow\s+(was|is|are|'s)\s+(your\s+)?(day|date|night|evening|morning)\b",
            t,
        ):
            return True
        if re.search(r"\bhow\s+are\s+you\b|\bhow's\s+it\s+going\b", t):
            return True
        if re.match(
            r"^(hi+|hello+|hey+|yo|sup|namaste)(\s+there)?[!?.]*$",
            t,
        ):
            return True
        if re.match(r"^good\s+(morning|evening|afternoon)\b", t):
            # good morning + calendar ask still possible
            if not self._is_date_query(t):
                return True
        return False

    def _is_date_query(self, t: str) -> bool:
        # Must be calendar — not "how was your date"
        if re.search(
            r"\bhow\s+(was|is|are|'s)\s+(your\s+)?(day|date|night)\b",
            t,
        ):
            return False
        patterns = (
            r"what(?:'s|\s+is)\s+(?:the\s+)?date",
            r"today'?s\s+date",
            r"current\s+date",
            r"what\s+date\s+is\s+today",
            r"tell\s+me\s+the\s+date",
            r"what\s+day\s+is\s+it",
            r"^today\s+date$",
            r"current\s+time",
            r"what(?:'s|\s+is)\s+(?:the\s+)?time\b",
        )
        return any(re.search(p, t) for p in patterns)


def classify_context_intent(text: str) -> dict[str, Any]:
    return ContextIntentClassifier().classify_detailed(text)
