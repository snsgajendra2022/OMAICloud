"""Conversation / project context for meaning grounding."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ContextSnapshot:
    recent_user: list[str] = field(default_factory=list)
    recent_assistant: list[str] = field(default_factory=list)
    project_hints: list[str] = field(default_factory=list)
    project_topic: str = ""
    resolved_followup: str = ""
    summary: str = ""


_SHORT_FOLLOW = re.compile(
    r"^(add|enable|fix|remove|update|create|make|build|docker|deploy|setup|"
    r"set up|integrate|implement)\b",
    re.I,
)
_PROJECT_HINT = re.compile(
    r"\b(building|working on|creating|developing|new project|this system)\b",
    re.I,
)
_OM = re.compile(r"\bom\s*ai\b", re.I)


def _topic_from_history(recent_user: list[str]) -> str:
    topic = ""
    for content in recent_user:
        if _OM.search(content):
            topic = "OM AI project"
        elif _PROJECT_HINT.search(content):
            topic = content.strip()[:120]
        elif len(content.split()) >= 4 and not _SHORT_FOLLOW.match(content):
            topic = topic or content.strip()[:100]
    return topic


def resolve_followup(current: str, topic: str) -> str:
    work = (current or "").strip()
    if not topic or not work:
        return ""
    if not (_SHORT_FOLLOW.match(work) and len(work.split()) <= 6):
        return ""
    if _OM.search(topic) or "om ai" in topic.lower():
        project = "OM AI project"
    else:
        project = topic
    m = re.match(
        r"^(add|enable|create|implement|build|make|fix|update)\s+(.+)$",
        work,
        re.I,
    )
    if m:
        feature = m.group(2).strip()
        verb = m.group(1).capitalize()
        if feature.lower() == "memory":
            return f"Memory system for {project}"
        return f"{verb} {feature} for {project}"
    if work.lower().startswith("docker"):
        return f"Prepare Docker environment for {project}"
    return f"{work} (for {project})"


def analyze_context(
    messages: list[dict[str, Any]] | None,
    *,
    project_instructions: str = "",
    memory_snippets: list[str] | None = None,
    current_text: str = "",
) -> ContextSnapshot:
    snap = ContextSnapshot()
    for m in messages or []:
        role = str(m.get("role") or "").lower()
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        if role == "user":
            snap.recent_user.append(content[:200])
        elif role == "assistant":
            snap.recent_assistant.append(content[:160])
    # Current turn is often already the last user message — keep priors.
    if current_text and snap.recent_user and snap.recent_user[-1][:80] == current_text.strip()[:80]:
        priors = snap.recent_user[:-1]
    else:
        priors = snap.recent_user
    snap.recent_user = snap.recent_user[-4:]
    snap.recent_assistant = snap.recent_assistant[-2:]

    snap.project_topic = _topic_from_history(priors[-4:] if priors else snap.recent_user[:-1])
    snap.resolved_followup = resolve_followup(current_text, snap.project_topic)

    if project_instructions.strip():
        snap.project_hints.append(project_instructions.strip()[:120])
    for mem in (memory_snippets or [])[:3]:
        if mem.strip():
            snap.project_hints.append(mem.strip()[:120])

    bits: list[str] = []
    if snap.resolved_followup:
        bits.append(f"Resolved follow-up: {snap.resolved_followup}")
    elif snap.project_topic:
        bits.append(f"Ongoing project: {snap.project_topic}")
    if snap.project_hints:
        bits.append("Context: " + " | ".join(snap.project_hints[:2]))
    if len(snap.recent_user) >= 2:
        bits.append("Do not treat this message as a standalone request.")
    snap.summary = " ".join(bits)
    return snap
