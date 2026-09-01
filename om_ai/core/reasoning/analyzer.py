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


PERFORMANCE_CAUSES = [
    "Database query",
    "Images",
    "JS bundle",
    "Server resources",
    "API latency",
    "Cache",
]


class IntentAnalyzer:
    _PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
        (
            "debug",
            "software",
            re.compile(r"\b(error|exception|fail|broken|fix|crash)\b", re.I),
        ),
        (
            "performance",
            "software",
            re.compile(r"\b(slow|latency|lagging|performance)\b", re.I),
        ),
        (
            "coding",
            "software",
            re.compile(
                r"\b(code|api|react|fastapi|bug|refactor|deploy|test|login|jsx|tsx|"
                r"typescript|javascript|docker|page)\b",
                re.I,
            ),
        ),
        (
            "architecture",
            "engineering",
            re.compile(r"\b(design|architect|system|scale|management|school|erp|sms)\b", re.I),
        ),
        ("research", "science", re.compile(r"\b(research|paper|physics|history|survey)\b", re.I)),
        ("business", "business", re.compile(r"\b(erp|crm|revenue|market|strategy)\b", re.I)),
    ]

    def analyze(self, text: str, *, messages: list[dict[str, Any]] | None = None) -> IntentResult:
        q = (text or "").strip()
        intent, domain = "general", "general"
        u_text = f"User wants help with: {q[:240]}"
        meta: dict[str, Any] = {"analyzer": "om-intent-v2"}

        try:
            from om_ai.understanding import understand_message

            u = understand_message(q, messages=messages)
            u_text = u.understood_meaning or u.goal or u_text
            mapped = {
                "debugging": "debug",
                "coding": "coding",
                "performance": "performance",
                "ui_design": "coding",
                "planning": "architecture",
                "knowledge": "research",
            }
            if u.intent in mapped:
                intent = mapped[u.intent]
                domain = "software" if intent in {"coding", "debug", "performance"} else u.category
            meta["understanding"] = {
                "intent": u.intent,
                "canonical": (u.meta or {}).get("canonical_intent"),
                "tokens": (u.meta or {}).get("tokens") or [],
                "goal": u.goal,
            }
            if u.goal:
                u_text = u.goal if len(u.goal) < 180 else u.understood_meaning
        except Exception:
            for name, dom, pat in self._PATTERNS:
                if pat.search(q):
                    intent, domain = name, dom
                    break

        if intent == "general":
            for name, dom, pat in self._PATTERNS:
                if pat.search(q):
                    intent, domain = name, dom
                    break

        if intent == "performance" or re.search(r"\b(website|site|app|page)\b.*\bslow\b|\bslow\b.*\b(website|site|app)\b", q, re.I):
            intent = "performance"
            domain = "software"
            meta["causes"] = list(PERFORMANCE_CAUSES)
            meta["avoid"] = "Do not immediately say increase server"
            u_text = (
                "Website/app is slow — diagnose causes (database, images, JS bundle, "
                "server, API latency, cache) before scaling hardware."
            )

        entities = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}", q)[:12]
        return IntentResult(
            understanding=u_text,
            intent=intent,
            domain=domain,
            entities=entities,
            meta=meta,
        )
