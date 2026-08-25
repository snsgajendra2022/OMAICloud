"""Conversation / project context for meaning grounding."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ContextSnapshot:
    recent_user: list[str] = field(default_factory=list)
    recent_assistant: list[str] = field(default_factory=list)
    project_hints: list[str] = field(default_factory=list)
    summary: str = ""


def analyze_context(
    messages: list[dict[str, Any]] | None,
    *,
    project_instructions: str = "",
    memory_snippets: list[str] | None = None,
) -> ContextSnapshot:
    snap = ContextSnapshot()
    for m in messages or []:
        role = str(m.get("role") or "").lower()
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            snap.recent_user.append(content[:160])
        elif role == "assistant":
            snap.recent_assistant.append(content[:160])
    snap.recent_user = snap.recent_user[-3:]
    snap.recent_assistant = snap.recent_assistant[-2:]

    if project_instructions.strip():
        snap.project_hints.append(project_instructions.strip()[:120])
    for mem in (memory_snippets or [])[:3]:
        if mem.strip():
            snap.project_hints.append(mem.strip()[:120])

    bits: list[str] = []
    if snap.project_hints:
        bits.append("Context: " + " | ".join(snap.project_hints[:2]))
    if len(snap.recent_user) >= 2:
        bits.append("Ongoing chat about recent user turns.")
    snap.summary = " ".join(bits)
    return snap
