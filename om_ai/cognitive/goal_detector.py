"""User goal detection with conversation context."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class GoalResult:
    goal: str
    resolved_text: str
    confidence: float
    used_context: bool
    project_topic: str = ""


_FOLLOW_UP = re.compile(
    r"^(add|enable|fix|remove|update|create|make|build|docker|deploy|setup|set up|"
    r"integrate|connect|implement|show|help|need)\b",
    re.I,
)
_SHORT = re.compile(r"^\s*\w+(?:\s+\w+){0,5}\s*$")
_PROJECT = re.compile(
    r"\b(building|working on|creating|developing|project)\b.*\b(om\s*ai|my\s+app|this\s+system|"
    r"this\s+project|website|dashboard|api)\b",
    re.I,
)
_OM = re.compile(r"\bom\s*ai\b", re.I)


def _prior_topic(messages: list[dict[str, Any]] | None) -> str:
    topic = ""
    for m in messages or []:
        if str(m.get("role") or "") != "user":
            continue
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        pm = _PROJECT.search(content)
        if pm:
            topic = content[:120]
        elif _OM.search(content):
            topic = "OM AI project"
        elif len(content.split()) >= 4 and not _FOLLOW_UP.match(content):
            topic = content[:100]
    return topic


def _project_label(topic: str) -> str:
    t = (topic or "").strip()
    if not t:
        return "the project"
    if re.search(r"\bom\s*ai\b", t, re.I):
        return "OM AI project"
    if re.search(r"\bnew project\b", t, re.I):
        return "the new project"
    return t


def _expand_docker_goal(text: str, topic: str) -> str:
    t = text.lower()
    label = _project_label(topic)
    if "dockerfile" in t or "docker file" in t:
        return f"Create Dockerfile for {label}"
    if any(w in t for w in ("deploy", "deployment", "production", "run")):
        return f"Deploy {label} using Docker"
    return f"Prepare Docker environment for {label}"


def _expand_feature_goal(text: str, topic: str) -> str:
    """Short follow-ups like 'add memory' → 'Add memory to OM AI project'."""
    feat = text.strip()
    if not topic:
        return feat.capitalize()
    # Strip leading verb for cleaner merge
    m = re.match(r"^(add|enable|create|implement|build|make)\s+(.+)$", feat, re.I)
    if m:
        feature = m.group(2).strip()
        label = "OM AI project" if re.search(r"\bom\s*ai\b", topic, re.I) else topic
        if feature.lower() in {"memory", "a memory", "memory system"}:
            return f"Memory system for {label}"
        return f"{m.group(1).capitalize()} {feature} for {label}"
    return f"{feat.capitalize()} (for {topic})"


def detect_goal(
    text: str,
    *,
    messages: list[dict[str, Any]] | None = None,
    corrected: str = "",
    base_goal: str = "",
) -> GoalResult:
    raw = (text or "").strip()
    work = (corrected or raw).strip()
    topic = _prior_topic(messages)
    used = False
    qlow = work.lower()
    is_short = bool(_SHORT.match(work)) and len(work.split()) <= 6
    is_follow = bool(_FOLLOW_UP.match(work))

    # Short follow-ups always prefer conversation context over a generic base goal.
    if is_short and (is_follow or topic) and topic:
        used = True
        if "docker" in qlow:
            goal = _expand_docker_goal(work, topic)
        else:
            goal = _expand_feature_goal(work, topic)
        resolved = f"{work} — in context of: {topic}"
        return GoalResult(
            goal=goal,
            resolved_text=resolved,
            confidence=0.88,
            used_context=True,
            project_topic=topic,
        )

    if re.search(r"\bdocker\b", qlow) and re.search(r"\b(this|system|project|app)\b", qlow):
        goal = _expand_docker_goal(work, topic or "this system")
        return GoalResult(
            goal=goal,
            resolved_text=work,
            confidence=0.82,
            used_context=bool(topic),
            project_topic=topic,
        )

    if re.search(r"\b(make|create|build|using)\b.*\b(login|signup|sign\s*in|register)\b", qlow):
        stack = "React " if "react" in qlow else ""
        page = "page" in qlow or "ui" in qlow
        if page:
            goal = f"Create {stack}login/signup UI with validation and auth integration".replace("  ", " ")
        else:
            goal = "Design full login system: frontend, backend API, database, auth, security, validation"
        return GoalResult(
            goal=goal.strip(),
            resolved_text=work,
            confidence=0.9,
            used_context=False,
            project_topic=topic,
        )

    if re.search(r"\b(slow|performance|lagging)\b", qlow) and re.search(
        r"\b(site|website|app|page)\b", qlow
    ):
        return GoalResult(
            goal="Diagnose website performance — check DB, assets, JS bundle, API latency, cache, server",
            resolved_text=work,
            confidence=0.86,
            used_context=False,
            project_topic=topic,
        )

    if base_goal and base_goal not in {"Help with the user's request.", ""}:
        return GoalResult(
            goal=base_goal,
            resolved_text=work,
            confidence=0.85,
            used_context=bool(topic),
            project_topic=topic,
        )

    return GoalResult(
        goal=base_goal or f"Help with: {work[:200]}",
        resolved_text=work,
        confidence=0.7,
        used_context=used,
        project_topic=topic,
    )
