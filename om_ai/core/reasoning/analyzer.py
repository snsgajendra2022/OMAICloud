"""Intent / understanding analyzer."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentResult:
    understanding: str
    intent: str
    domain: str
    entities: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "understanding": self.understanding,
            "intent": self.intent,
            "domain": self.domain,
            "entities": self.entities,
            "meta": self.meta,
        }


class IntentAnalyzer:
    _PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
        ("coding", "software", re.compile(r"\b(code|api|react|fastapi|bug|refactor|deploy|test)\b", re.I)),
        ("research", "science", re.compile(r"\b(research|paper|physics|history|survey)\b", re.I)),
        ("architecture", "engineering", re.compile(r"\b(design|architect|system|scale)\b", re.I)),
        ("debug", "software", re.compile(r"\b(error|exception|fail|broken|fix)\b", re.I)),
        ("business", "business", re.compile(r"\b(erp|crm|revenue|market|strategy)\b", re.I)),
    ]

    def analyze(self, text: str) -> IntentResult:
        q = (text or "").strip()
        intent, domain = "general", "general"
        for name, dom, pat in self._PATTERNS:
            if pat.search(q):
                intent, domain = name, dom
                break
        entities = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}", q)[:12]
        return IntentResult(
            understanding=f"User wants help with: {q[:240]}",
            intent=intent,
            domain=domain,
            entities=entities,
            meta={"analyzer": "om-intent-v1"},
        )
