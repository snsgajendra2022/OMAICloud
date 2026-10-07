"""Shared: build a real answer from brain / facts / reasoning / coding / model.

Never invent canned outlines like "Core idea / How it works".
"""
from __future__ import annotations

import os
import re
from typing import Any


_STATIC_SMELL = re.compile(
    r"(here.?s a clear take|core idea\s*(→|->|/)|want a deeper dive|"
    r"ask for a deeper dive|is best understood by|plain-language explanation|"
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
    r"prefer typescript when building ui|"
    r"belongs in the om genesis knowledge map|"
    r"variant focus:|"
    r"map this to om ai modules first|"
    r"bio-digital ideas labeled as research|"
    r"the issue may come from incorrect assumptions|"
    r"here'?s the direct path for|"
    r"that last draft wasn'?t solid|"
    r"i hear you, brother|"
    r"tell me straight what you need|"
    r"clarify goal, then give a direct actionable answer)",
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
    try:
        from om_ai.core.chat_intelligence.stub_detect import is_solution_stub

        if is_solution_stub(t):
            return True
    except Exception:
        pass
    try:
        from om_ai.runtime.public_reply import looks_like_genesis_template

        if looks_like_genesis_template(t):
            return True
    except Exception:
        pass
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
        ans = str(hit.get("answer") or "")
        src = str(hit.get("source") or "").lower()
        if "genesis" in src:
            return None
        try:
            from om_ai.runtime.public_reply import looks_like_genesis_template

            if looks_like_genesis_template(ans):
                return None
        except Exception:
            pass
        return _accept(ans)
    except Exception:
        return None


def from_helpful_defaults(q: str) -> str | None:
    """Deterministic clear answers for common user asks when retrieval/model fail."""
    low = (q or "").lower().strip()
    if not low:
        return None

    # Gibberish / keyboard mash
    letters = re.findall(r"[a-z]", low)
    if len(low.split()) <= 2 and len(letters) >= 6:
        vowels = sum(1 for c in letters if c in "aeiou")
        if vowels / max(len(letters), 1) < 0.25:
            return (
                "I couldn’t catch that clearly. "
                "Say it again naturally — I’m listening."
            )

    # Greetings / casual openers
    if re.match(
        r"^(hi+|hii+|hello|hey+|yo|sup|namaste|hola|good\s*(morning|evening|afternoon))\b",
        low,
    ):
        return "Hey — I'm OM. What's on your mind?"

    # Hindi / Hinglish casual "what is this"
    if re.search(
        r"(?i)\b(kya\s+hai|are\s+kya|yeh?\s+kya|kya\s+ho\s+raha|samajh\s+nahi)\b",
        low,
    ):
        return (
            "Main yahin hoon. Bataiye kya dekhna / samajhna hai — "
            "seedha jawab dunga."
        )

    # Knowledge / "show what you know"
    if re.search(
        r"(?i)\b(knowledge|full\s+knowledge|what\s+do\s+you\s+know|"
        r"display\s+your\s+(full\s+)?knowledge|master\s+update|"
        r"moaster\s+update)\b",
        low,
    ):
        return (
            "I can pull from local OM knowledge, memory, tools, and reasoning — "
            "not a single canned dump.\n\n"
            "Ask a concrete topic (e.g. Zoom setup, Python bug, project plan) "
            "and I’ll answer with what I know plus next steps."
        )

    if re.search(r"\breact\b", low) and re.search(
        r"\b(latest|current|lestest|lest|new|verion|version)\b", low
    ):
        return (
            "The current major React release line is **React 19**.\n\n"
            "Check the exact latest patch on:\n"
            "- https://react.dev/versions\n"
            "- https://www.npmjs.com/package/react\n\n"
            "Install with: `npm install react@latest react-dom@latest`"
        )

    if re.search(r"\breact\b", low) and re.search(
        r"\b(create|start|setup|set\s*up|project|app|vite)\b", low
    ):
        return (
            "Here’s the standard way to create a React project:\n\n"
            "```bash\nnpm create vite@latest my-app -- --template react\n"
            "cd my-app\nnpm install\nnpm run dev\n```\n\n"
            "Or with TypeScript:\n\n"
            "```bash\nnpm create vite@latest my-app -- --template react-ts\n```\n\n"
            "Then open the local URL Vite prints (usually http://localhost:5173)."
        )

    if re.search(r"\breact\b", low) and re.search(r"\bwhat\b", low):
        return from_facts(q) or (
            "**React** is a JavaScript library for building user interfaces. "
            "You build UI from reusable **components**. When state changes, "
            "React updates only the parts that need to change.\n\n"
            "Use it for web apps. **React Native** uses the same idea for iOS/Android."
        )

    if re.search(r"\b(dashbord|dashabord|dashboard|dash\s*board)\b", low) and re.search(
        r"\b(create|build|make|design)\b", low
    ):
        return (
            "I can help you create a dashboard. A solid starter path:\n\n"
            "1. Create a React app (Vite)\n"
            "2. Add a layout: sidebar + top bar + main content\n"
            "3. Add pages/widgets (stats cards, charts, tables)\n"
            "4. Fetch data from an API\n\n"
            "Tell me your stack (React / Next.js / plain HTML) and I’ll give the first files."
        )

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

        # Prefer helpful defaults even when short (greetings / hinglish)
        try:
            default_hit = from_helpful_defaults(q)
            if default_hit and not looks_like_static_reply(default_hit):
                if len(default_hit.strip()) >= 12:
                    return default_hit.strip()
        except Exception:
            pass

    order = []
    if prefer_coding:
        order = [from_facts, from_coding_brain, from_reasoning, from_brain, from_model]
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
        # from_helpful_defaults may be short; others need _accept
        if fn is from_facts and hit:
            return hit
        hit = _accept(hit)
        if hit:
            return hit
    return None
