"""Response Formatting Engine — short vs structured vs table vs highlights."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class FormatSpec:
    mode: str  # short | technical | comparison | diagnostic
    highlight: list[str]
    sections: list[str]


_COMPARE = re.compile(r"\b(vs\.?|versus|compare|difference between)\b", re.I)
_SIMPLE = re.compile(r"^(what is|who is|define|meaning of)\b", re.I)
_TECH = re.compile(
    r"\b(how to|implement|architecture|login|dashboard|api|docker|deploy)\b",
    re.I,
)


def decide_format(question: str, *, intent: str = "chat", audience: str = "developer") -> FormatSpec:
    q = (question or "").strip()
    if _COMPARE.search(q):
        return FormatSpec(
            mode="comparison",
            highlight=[],
            sections=["Feature", "Option A", "Option B"],
        )
    if intent == "performance" or re.search(r"\b(slow|latency)\b", q, re.I):
        return FormatSpec(
            mode="diagnostic",
            highlight=["Do not jump to scaling the server first."],
            sections=["Understanding", "Possible causes", "What to check", "Next steps"],
        )
    if _SIMPLE.match(q) and len(q.split()) <= 10 and audience == "beginner":
        return FormatSpec(mode="short", highlight=[], sections=[])
    if intent in {"coding", "debug", "architecture", "debugging"} or _TECH.search(q):
        return FormatSpec(
            mode="technical",
            highlight=["Do not expose API keys."],
            sections=[
                "Understanding",
                "Architecture",
                "File structure",
                "Implementation",
                "Configuration",
                "Installation",
                "Testing",
                "Next Steps",
            ],
        )
    if audience == "expert":
        return FormatSpec(
            mode="technical",
            highlight=[],
            sections=["Understanding", "Analysis", "Trade-offs", "Next Steps"],
        )
    return FormatSpec(mode="short" if len(q.split()) <= 8 else "technical", highlight=[], sections=[])


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not headers:
        return ""
    head = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(c) + " |" for c in rows]
    return "\n".join([head, sep, *body])


def highlight_important(text: str, notes: list[str] | None = None) -> str:
    raw = (text or "").rstrip()
    extras = [n for n in (notes or []) if n and f"**Important:** {n}" not in raw]
    if not extras:
        if re.search(r"(?im)^important:", raw):
            return raw
        return raw
    block = "\n".join(f"**Important:** {n}" for n in extras)
    return f"{raw}\n\n{block}\n"


def apply_format(
    text: str,
    spec: FormatSpec,
    *,
    understanding: str = "",
    already_structured: bool | None = None,
) -> str:
    raw = (text or "").strip()
    if not raw:
        return raw
    structured = (
        already_structured
        if already_structured is not None
        else bool(re.search(r"(?m)^#{1,3}\s|```", raw))
    )
    if spec.mode == "short":
        first = raw.split("\n\n")[0].strip()
        return highlight_important(first, spec.highlight)

    if spec.mode == "comparison" and not structured:
        # Leave body; caller may pass a table. Ensure a table header exists.
        if "|" not in raw:
            raw = raw + "\n\n" + markdown_table(
                ["Feature", "A", "B"],
                [["Scope", "See analysis above", "See analysis above"]],
            )

    if spec.mode in {"technical", "diagnostic"} and not structured and spec.sections:
        parts = [f"## {spec.sections[0]}\n{understanding or 'See request.'}", f"## {spec.sections[1]}\n{raw}"]
        for title in spec.sections[2:]:
            if title.lower() in raw.lower():
                continue
            if title == "Testing":
                parts.append("## Testing\n- Happy path\n- Error path")
            elif title == "Next Steps":
                parts.append("## Next Steps\n- Verify in your environment")
            elif title == "What to check":
                parts.append(
                    "## What to check\n"
                    "- Database query\n- Images\n- JS bundle\n"
                    "- Server resources\n- API latency\n- Cache"
                )
        raw = "\n\n".join(parts)

    return highlight_important(raw, spec.highlight)


def format_reply(
    text: str,
    question: str,
    *,
    intent: str = "chat",
    audience: str = "developer",
    understanding: str = "",
) -> str:
    spec = decide_format(question, intent=intent, audience=audience)
    return apply_format(text, spec, understanding=understanding)
