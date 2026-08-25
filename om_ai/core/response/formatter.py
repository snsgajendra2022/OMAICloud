"""Response formatter — wraps response_engine."""
from __future__ import annotations

from typing import Any


def format_response(text: str, *, intent: str = "chat", enhance: bool = True) -> str:
    try:
        from om_ai.response_engine import format_assistant_reply

        return format_assistant_reply(text or "", intent=intent, enhance=enhance)
    except Exception:
        return (text or "").strip()


def format_structured(sections: dict[str, Any]) -> str:
    order = (
        "understanding",
        "analysis",
        "architecture",
        "implementation",
        "validation",
        "next_steps",
    )
    lines: list[str] = []
    for key in order:
        val = sections.get(key)
        if not val:
            continue
        title = key.replace("_", " ").title()
        lines.append(f"## {title}")
        if isinstance(val, list):
            lines.extend(f"- {x}" for x in val)
        else:
            lines.append(str(val))
        lines.append("")
    return "\n".join(lines).strip() + ("\n" if lines else "")
