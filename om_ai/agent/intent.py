"""Intent classification for OM Agent Brain (no external LLM)."""
from __future__ import annotations

import re
from enum import Enum


class ChatIntent(str, Enum):
    greeting = "greeting"
    identity = "identity"
    memory = "memory"
    knowledge = "knowledge"
    coding = "coding"
    agent = "agent"
    chat = "chat"


_CODING = re.compile(
    r"\b("
    r"code|coding|bug|debug|error|stack\s*trace|exception|"
    r"function|class|api|endpoint|refactor|implement|typescript|javascript|"
    r"python|react|java|sql|docker|kubernetes|git|pr\b|pull\s+request|"
    r"write\s+(?:a\s+)?(?:script|function|component|test)|fix\s+(?:my\s+)?(?:code|bug)"
    r")\b",
    re.IGNORECASE,
)

_AGENT = re.compile(
    r"\b("
    r"plan|steps?|workflow|automate|run\s+(?:a\s+)?(?:command|shell)|"
    r"search\s+(?:my\s+)?(?:knowledge|docs|files)|scan\s+(?:the\s+)?project|"
    r"use\s+tools?|multi[\s-]?step|break\s+(?:this\s+)?down|"
    r"help\s+me\s+(?:build|create|set\s+up|investigate)"
    r")\b",
    re.IGNORECASE,
)

_KNOWLEDGE = re.compile(
    r"\b("
    r"what\s+is|what\s+are|who\s+is|explain|define|how\s+(?:do|does|to)|"
    r"capital\s+of|meaning\s+of|difference\s+between|compare|"
    r"documentation|according\s+to|in\s+(?:my\s+)?(?:docs|knowledge|notes)"
    r")\b",
    re.IGNORECASE,
)

_MEMORY = re.compile(
    r"\b("
    r"remember|my\s+name\s+is|i\s+prefer|what\s+do\s+you\s+remember|"
    r"what(?:'s| is)\s+my\s+name|do\s+you\s+know\s+(?:my|about\s+me)"
    r")\b",
    re.IGNORECASE,
)

_IDENTITY = re.compile(
    r"\b("
    r"who\s+are\s+you|what\s+are\s+you|what\s+can\s+you\s+do|"
    r"about\s+om|om[\s-]?1\.?0|are\s+you\s+chatgpt"
    r")\b",
    re.IGNORECASE,
)

_GREETING = re.compile(
    r"^(hi+|hello|hey+|yo|sup|namaste|नमस्ते|good\s+mor\w*|good\s+evening|"
    r"good\s+afternoon|how\s+are\s+you)\b",
    re.IGNORECASE,
)


def classify_intent(user_text: str) -> ChatIntent:
    t = (user_text or "").strip()
    if not t:
        return ChatIntent.chat
    if _GREETING.match(t) and len(t.split()) <= 8:
        return ChatIntent.greeting
    if _IDENTITY.search(t):
        return ChatIntent.identity
    if _MEMORY.search(t):
        return ChatIntent.memory
    if _CODING.search(t):
        return ChatIntent.coding
    if _AGENT.search(t):
        return ChatIntent.agent
    if _KNOWLEDGE.search(t):
        return ChatIntent.knowledge
    return ChatIntent.chat
