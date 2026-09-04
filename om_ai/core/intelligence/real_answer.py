"""Shared: build a real answer from brain / facts / reasoning / coding / model.

Never invent canned outlines like "Core idea / How it works".
"""
from __future__ import annotations

import os
import re
from typing import Any


_STATIC_SMELL = re.compile(
    r"(here.?s a clear take|core idea\s*(→|->|/)|want a deeper dive|"
    r"want a beginner version|define the outcome|define success metrics|"
    r"current state\s*\n.*options|i can help implement this|"
    r"tell me constraints \(framework|"
    r"here is a clear, useful answer grounded|"
    r"share stack constraints and i.?ll emit|"
    r"what should i produce first|"
    r"break it into actionable steps|"
    r"deliver the first useful artifact|"
    r"here are practical suggestions for your request|"
    r"pick constraints \(time, budget|"
    r"restatement of the outcome|"
    r"produce production-quality output|"
    r"prefer typescript when building ui)",
    re.I | re.S,
)


def looks_like_static_reply(text: str) -> bool:
    """True for canned *outline* dumps — not for normal greetings or short answers."""
    t = (text or "").strip()
    if not t:
        return False  # empty is handled separately; do not label greetings path as "static"
    # Short natural greetings are valid replies
    if len(t) < 120 and re.match(
        r"^(hi|hey|hello|namaste|good (morning|evening|afternoon))\b",
        t,
        re.I,
    ):
        return False
    return bool(_STATIC_SMELL.search(t))


def _looks_like_garbage(text: str) -> bool:
    """Reject model garble and internal pipeline chrome."""
    t = (text or "").strip()
    if not t:
        return True
    # Allow short greetings
    if len(t) < 160 and re.match(
        r"^(hi|hey|hello|namaste|i('m| am) om)\b",
        t,
        re.I,
    ):
        return False
    # Allow fenced code / markdown file dumps from tools
    if "```" in t or t.lstrip().startswith("## Prompt for:"):
        return False
    if looks_like_static_reply(t):
        return True
    try:
        from om_ai.core.response.response_formatter import looks_like_pipeline_dump

        if looks_like_pipeline_dump(t):
            return True
    except Exception:
        pass
    try:
        from om_ai.runtime.chat_orchestrator import is_low_quality_reply

        if is_low_quality_reply(t):
            return True
    except Exception:
        pass
    # Heuristic: too many short nonsense tokens
    words = re.findall(r"[A-Za-z]+", t)
    if len(words) >= 20:
        weird = sum(1 for w in words if len(w) >= 8 and not re.search(r"[aeiouAEIOU]{1}", w[1:]))
        if weird / max(1, len(words)) > 0.35:
            return True
    return False


def _accept(ans: str | None) -> str | None:
    if not ans:
        return None
    a = ans.strip()
    if len(a) < 40 or _looks_like_garbage(a):
        return None
    return a


def _static_ok() -> bool:
    return os.environ.get("OM_STATIC_TEMPLATES", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def from_facts(q: str) -> str | None:
    try:
        from om_ai.knowledge.facts import lookup_fact

        hit = lookup_fact(q)
        if hit and hit.get("answer"):
            return _accept(str(hit["answer"]))
    except Exception:
        pass
    return None


def from_brain(q: str, *, min_score: float = 0.45) -> str | None:
    try:
        from om_ai.brain.dataset_engine import retrieve_answer

        hit = retrieve_answer(q, min_score=min_score)
        if not hit:
            return None
        return _accept(str(hit.get("answer") or ""))
    except Exception:
        return None


def from_reasoning(q: str) -> str | None:
    try:
        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

        r = run_reasoning_pipeline(q, retrieve=True)
        sol = str(r.get("solution") or "").strip()
        md = str(r.get("markdown") or "").strip()
        meta = r.get("meta") or {}
        if meta.get("source") == "static_demo" and not _static_ok():
            return None
        # Prefer solution body; full markdown is often internal chrome
        if sol and "No strong corpus match" not in sol:
            hit = _accept(sol)
            if hit:
                return hit
        if "```" in md:
            hit = _accept(md)
            if hit:
                return hit
    except Exception:
        pass
    return None


def from_coding_brain(q: str, *, root: str = ".") -> str | None:
    qlow = (q or "").lower()
    codingish = any(
        w in qlow
        for w in (
            "code",
            "python",
            "react",
            "javascript",
            "typescript",
            "api",
            "function",
            "class",
            "bug",
            "fix",
            "implement",
            "login",
            "signup",
            "component",
            "script",
            "program",
            "fastapi",
            "django",
            "html",
            "css",
        )
    )
    if not codingish:
        return None
    try:
        from om_ai.coding_brain import handle

        out = handle(q, root=root, dry_run=True)
        parts: list[str] = []
        md = str(out.get("reasoning_markdown") or "").strip()
        plan = out.get("plan") or {}
        # Prefer solution with code from reasoning
        if md and "```" in md:
            parts.append(md)
        elif md and len(md) > 200 and not looks_like_static_reply(md):
            parts.append(md)
        # Coding agent plan summary
        if isinstance(plan, dict):
            summary = str(plan.get("summary") or plan.get("markdown") or "").strip()
            steps = plan.get("steps") or plan.get("plan") or []
            if summary and not looks_like_static_reply(summary):
                parts.append(summary)
            if steps and not parts:
                lines = ["## Coding plan", ""]
                for i, s in enumerate(steps[:8], 1):
                    lines.append(f"{i}. {s}")
                parts.append("\n".join(lines))
        body = "\n\n".join(p for p in parts if p).strip()
        return _accept(body)
    except Exception:
        pass
    return None


def from_model(q: str) -> str | None:
    if os.environ.get("OM_SOLVER_USE_MODEL", "1").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return None
    # Avoid recursion when called from inside chat_reply pipelines
    if os.environ.get("_OM_IN_CHAT_REPLY", "0") == "1":
        return None
    try:
        from om_ai.backends.om_native import OMNativeBackend

        backend = OMNativeBackend()
        prompt = (
            "You are OM. Answer directly with useful content. "
            "For code requests, write working code in fenced blocks.\n\n"
            f"User: {(q or '').strip()}\n\nAssistant:"
        )
        text = backend.generate(
            prompt,
            max_new_tokens=int(os.environ.get("OM_CHAT_MAX_NEW_TOKENS") or 256),
            temperature=0.35,
        )
        return _accept(text)
    except Exception:
        return None


def build_real_answer(
    question: str,
    *,
    prefer_coding: bool = False,
    knowledge_packets: list[dict[str, Any]] | None = None,
    root: str = ".",
) -> str | None:
    """Return a concrete answer, or None so callers can defer to the next pipeline."""
    q = (question or "").strip()
    if not q:
        return None

    # Prefer fact packets already retrieved
    for p in knowledge_packets or []:
        if p.get("source") in {"facts", "calendar_clock"} and p.get("texts"):
            hit = _accept(str(p["texts"][0]))
            if hit:
                return hit

    order = []
    if prefer_coding:
        order = [from_coding_brain, from_reasoning, from_brain, from_facts, from_model]
    else:
        order = [from_facts, from_brain, from_coding_brain, from_reasoning, from_model]

    for fn in order:
        try:
            if fn is from_coding_brain:
                hit = from_coding_brain(q, root=root)
            else:
                hit = fn(q)  # type: ignore[operator]
        except Exception:
            hit = None
        hit = _accept(hit)
        if hit:
            return hit
    return None
