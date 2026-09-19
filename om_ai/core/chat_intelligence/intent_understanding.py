"""Intent understanding for OM Chat Intelligence."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentResult:
    intent: str
    confidence: float
    strategy: str
    needs_model: bool = True
    needs_details: bool = False
    domain: str = "general"
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "strategy": self.strategy,
            "needs_model": self.needs_model,
            "needs_details": self.needs_details,
            "domain": self.domain,
            "signals": list(self.signals),
        }


class IntentUnderstanding:
    """Classify user intent for ChatGPT-style routing."""

    GREETING = re.compile(
        r"^\s*(hi|hello|hey|yo|sup|good\s*(morning|afternoon|evening|night)|"
        r"how\s+are\s+you|what'?s\s+up|namaste|hola)\b",
        re.I,
    )
    IDENTITY = re.compile(
        r"\b(who\s+are\s+you|what\s+are\s+you|your\s+name|are\s+you\s+(an?\s+)?ai)\b",
        re.I,
    )
    # User's own name — must win over "what is …" explain templates
    USER_NAME = re.compile(
        r"(?i)\b("
        r"what(?:'s|\s+is)\s+my\s+name|"
        r"do\s+you\s+know\s+my\s+name|"
        r"what\s+do\s+you\s+call\s+me|"
        r"mera\s+naam(\s+kya)?|"
        r"my\s+name\s+is\s+\w+"
        r")\b"
    )
    USER_NAME_SET = re.compile(
        r"(?i)\b(?:my\s+name\s+is|call\s+me|mera\s+naam(?:\s+hai)?)\s+([A-Za-z][A-Za-z\s]{0,40})"
    )
    THANKS = re.compile(r"^\s*(thanks|thank\s+you|thx|ty)\b", re.I)
    BYE = re.compile(r"^\s*(bye|goodbye|see\s+you|later)\b", re.I)
    DEBUG = re.compile(
        r"\b(error|bug|blank\s+page|crash|not\s+working|broken|exception|"
        r"stack\s*trace|fails?|undefined|null\s+reference)\b",
        re.I,
    )
    CODE = re.compile(
        r"\b(react|python|javascript|typescript|code|function|api|sql|"
        r"component|hook|docker|kubernetes|css|html)\b",
        re.I,
    )
    HOWTO = re.compile(r"\b(how\s+(do|to|can)|steps?|guide|tutorial|implement)\b", re.I)
    COMPARE = re.compile(r"\b(compare|vs\.?|versus|difference|better)\b", re.I)
    EXPLAIN = re.compile(r"\b(what\s+is|explain|define|meaning|why)\b", re.I)
    FOLLOWUP = re.compile(
        r"^\s*(and|also|then|what\s+about|how\s+about|continue|more|"
        r"yes|no|ok|okay|that|this)\b",
        re.I,
    )

    def understand(self, message: str, *, history: list[dict] | None = None) -> IntentResult:
        text = (message or "").strip()
        low = text.lower()
        signals: list[str] = []

        if not text:
            return IntentResult(
                intent="empty",
                confidence=1.0,
                strategy="ask_clarify",
                needs_model=False,
            )

        if self.IDENTITY.search(text):
            return IntentResult(
                intent="identity",
                confidence=0.98,
                strategy="friendly_identity",
                needs_model=False,
                signals=["identity"],
            )
        # Remember name before recall / explain
        if self.USER_NAME_SET.search(text):
            return IntentResult(
                intent="user_name_set",
                confidence=0.97,
                strategy="personal_memory",
                needs_model=False,
                signals=["user_name", "personal", "set"],
            )
        if self.USER_NAME.search(text) or re.search(r"(?i)\bmy\s+name\b", text):
            return IntentResult(
                intent="user_name",
                confidence=0.97,
                strategy="personal_memory",
                needs_model=False,
                signals=["user_name", "personal"],
            )
        if self.GREETING.search(text) and len(text.split()) <= 8:
            kind = "greeting"
            if "morning" in low:
                kind = "morning"
            elif "evening" in low or "night" in low:
                kind = "evening"
            elif "afternoon" in low:
                kind = "afternoon"
            return IntentResult(
                intent=kind,
                confidence=0.97,
                strategy="friendly_conversation",
                needs_model=False,
                signals=["greeting"],
            )
        if self.THANKS.search(text) and len(text.split()) <= 6:
            return IntentResult(
                intent="thanks",
                confidence=0.95,
                strategy="friendly_conversation",
                needs_model=False,
                signals=["thanks"],
            )
        if self.BYE.search(text) and len(text.split()) <= 6:
            return IntentResult(
                intent="goodbye",
                confidence=0.95,
                strategy="friendly_conversation",
                needs_model=False,
                signals=["goodbye"],
            )

        if self.DEBUG.search(text):
            signals.append("debug")
            domain = "coding" if self.CODE.search(text) else "troubleshooting"
            return IntentResult(
                intent="debugging",
                confidence=0.9,
                strategy="technical_solution",
                needs_model=True,
                needs_details=len(text.split()) < 8,
                domain=domain,
                signals=signals,
            )
        if self.CODE.search(text) and (self.HOWTO.search(text) or "build" in low or "create" in low):
            return IntentResult(
                intent="coding",
                confidence=0.88,
                strategy="code_solution",
                needs_model=True,
                domain="coding",
                signals=["code", "howto"],
            )
        if self.COMPARE.search(text):
            return IntentResult(
                intent="comparison",
                confidence=0.86,
                strategy="comparison",
                needs_model=True,
                signals=["compare"],
            )
        if self.HOWTO.search(text):
            return IntentResult(
                intent="howto",
                confidence=0.85,
                strategy="step_by_step",
                needs_model=True,
                signals=["howto"],
            )
        if self.EXPLAIN.search(text):
            # Never treat personal-name questions as concept explain
            if self.USER_NAME.search(text) or re.search(r"(?i)\bmy\s+name\b", text):
                return IntentResult(
                    intent="user_name",
                    confidence=0.96,
                    strategy="personal_memory",
                    needs_model=False,
                    signals=["user_name", "personal"],
                )
            return IntentResult(
                intent="explain",
                confidence=0.84,
                strategy="explanation",
                needs_model=True,
                signals=["explain"],
            )

        if history and self.FOLLOWUP.search(text) and len(text.split()) <= 12:
            return IntentResult(
                intent="followup",
                confidence=0.8,
                strategy="contextual_continue",
                needs_model=True,
                signals=["followup"],
            )

        if "?" in text or low.startswith(("what", "how", "why", "when", "where", "can ", "could ")):
            return IntentResult(
                intent="question",
                confidence=0.75,
                strategy="direct_answer",
                needs_model=True,
                signals=["question"],
            )

        return IntentResult(
            intent="chat",
            confidence=0.6,
            strategy="general_assist",
            needs_model=True,
            signals=["general"],
        )
