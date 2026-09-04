"""Route intent → capability. Real answers only — never canned outlines."""
from __future__ import annotations

import os
import re
from typing import Any, Callable

from om_ai.core.intelligence.real_answer import (
    build_real_answer,
    looks_like_static_reply,
)


INTENT_CAPABILITY: dict[str, str] = {
    "vision_analysis": "vision",
    "date_request": "date",
    "prompt_generation": "prompt_generator",
    "recommendation": "recommendation",
    "code_creation": "coding",
    "explanation": "research",
    "debugging": "coding",
    "research": "research",
    "planning": "planning",
    "comparison": "analysis",
    "calculation": "calculator",
    "conversation": "chat",
    "question": "research",
    "creation": "coding",
    "generation": "prompt_generator",
    "unclear": "clarify",
}


def _static_ok() -> bool:
    return os.environ.get("OM_STATIC_TEMPLATES", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def looks_like_static_capability_reply(text: str) -> bool:
    return looks_like_static_reply(text)


def _cap_date(_q: str, _ctx: dict, _u: dict) -> str:
    """Live clock — not a stored reply."""
    from datetime import datetime

    try:
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        now = datetime.now().astimezone()
    return f"Today's date is {now.strftime('%A, %d %B %Y')}.\n"


def _extract_prompt_topic(q: str) -> str:
    topic = (q or "").strip()
    for noise in (
        "create prompt for",
        "make prompt for",
        "write prompt for",
        "generate prompt for",
        "create a prompt for",
        "create prompt",
        "make prompt",
        "write prompt",
        "generate prompt",
    ):
        if noise in topic.lower():
            topic = topic.lower().split(noise, 1)[-1].strip(" :.-")
            break
    return topic or q.strip()


def _cap_prompt(q: str, ctx: dict, u: dict) -> str:
    """Build a prompt from the user's topic — no fixed Goals/Constraints skeleton."""
    from om_ai.core.intelligence.real_answer import _looks_like_garbage

    real = build_real_answer(q, prefer_coding=True)
    if real and not _looks_like_garbage(real) and (
        "prompt" in real.lower() or "```" in real or len(real) > 120
    ):
        # Only use corpus/reasoning if it's actually useful for this ask
        if any(w in real.lower() for w in _extract_prompt_topic(q).lower().split()[:3] if len(w) > 2):
            return real + "\n"

    topic = _extract_prompt_topic(q)
    project = str(ctx.get("project_hint") or "").strip()
    lines = [
        f"## Prompt for: {topic}",
        "",
        f"Act as a specialist in {topic}.",
        f"User goal: {q.strip()}",
    ]
    if project:
        lines.append(f"Project context: {project}")
    lines.extend(
        [
            "",
            "Deliver a concrete solution for this exact goal — code, steps, or design as needed.",
            "State assumptions. Prefer working examples over placeholders.",
        ]
    )
    return "\n".join(lines) + "\n"


def _cap_recommendation(q: str, ctx: dict, u: dict) -> str:
    real = build_real_answer(q)
    return (real + "\n") if real else ""


def _cap_coding(q: str, ctx: dict, u: dict) -> str:
    root = str(ctx.get("project_root") or ctx.get("root") or ".")
    real = build_real_answer(q, prefer_coding=True, root=root)
    return (real + "\n") if real else ""


def _cap_research(q: str, ctx: dict, u: dict) -> str:
    real = build_real_answer(q)
    return (real + "\n") if real else ""


def _cap_planning(q: str, ctx: dict, u: dict) -> str:
    real = build_real_answer(q, prefer_coding=True)
    return (real + "\n") if real else ""


def _cap_analysis(q: str, ctx: dict, u: dict) -> str:
    real = build_real_answer(q)
    return (real + "\n") if real else ""


def _cap_calculator(q: str, ctx: dict, u: dict) -> str:
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", q, re.I)
    if m:
        pct, base = float(m.group(1)), float(m.group(2))
        return f"{pct}% of {base:g} = {(pct / 100.0) * base:g}\n"
    expr = re.search(r"([\d\.\s\+\-\*\/\(\)]+)", q)
    if expr:
        raw = expr.group(1).strip()
        if re.fullmatch(r"[\d\.\s\+\-\*\/\(\)]+", raw) and any(c.isdigit() for c in raw):
            try:
                val = eval(raw, {"__builtins__": {}}, {})  # noqa: S307
                if isinstance(val, (int, float)):
                    return f"{raw.strip()} = {val:g}\n"
            except Exception:
                pass
    real = build_real_answer(q)
    return (real + "\n") if real else ""


def _cap_chat(q: str, ctx: dict, u: dict) -> str:
    qlow = (q or "").strip().lower()
    # Any greeting spelling (hi, hii, hello, hey…) — natural reply, never empty
    if re.match(r"^(hi+|hello+|hey+|yo|sup|namaste|hola)[!?.]*$", qlow) or re.match(
        r"^(good\s+(morning|evening|afternoon))\b", qlow
    ):
        return "Hello — I’m OM. What should we work on?\n"
    real = build_real_answer(q)
    if real:
        return real + "\n"
    # Never leave the user with a blank bubble
    try:
        from om_ai.agent.verifier import compose_fallback

        fb = (compose_fallback(intent="chat", user_text=q) or "").strip()
        if fb:
            return fb + "\n"
    except Exception:
        pass
    return ""


def _cap_clarify(q: str, ctx: dict, u: dict) -> str:
    """Never trap real questions — and never leave greetings blank."""
    qlow = (q or "").strip().lower()
    if re.match(r"^(hi+|hello+|hey+|yo|sup|namaste|hola)[!?.]*$", qlow):
        return "Hello — I’m OM. What should we work on?\n"
    real = build_real_answer(q)
    if real:
        return real + "\n"
    try:
        from om_ai.agent.verifier import compose_fallback

        fb = (compose_fallback(intent="chat", user_text=q) or "").strip()
        if fb and "Core idea" not in fb and "## Understanding" not in fb:
            return fb + "\n"
    except Exception:
        pass
    return ""


def _cap_vision(q: str, ctx: dict, u: dict) -> str:
    path = str(ctx.get("image_path") or ctx.get("attachment") or "").strip()
    if path:
        try:
            from om_ai.operating_intelligence import perception_bridge

            out = getattr(perception_bridge, "analyze_image", None)
            if callable(out):
                result = out(path, question=q)
                if isinstance(result, dict) and result.get("summary"):
                    return str(result["summary"]).strip() + "\n"
                if isinstance(result, str) and len(result) > 20:
                    return result.strip() + "\n"
        except Exception:
            pass
    real = build_real_answer(q)
    return (real + "\n") if real else ""


CAPABILITY_HANDLERS: dict[str, Callable[[str, dict, dict], str]] = {
    "date": _cap_date,
    "prompt_generator": _cap_prompt,
    "recommendation": _cap_recommendation,
    "coding": _cap_coding,
    "research": _cap_research,
    "planning": _cap_planning,
    "analysis": _cap_analysis,
    "calculator": _cap_calculator,
    "chat": _cap_chat,
    "clarify": _cap_clarify,
    "vision": _cap_vision,
}


class CapabilityRouter:
    def route(self, intent: dict[str, Any]) -> dict[str, Any]:
        key = str(intent.get("intent") or intent.get("canonical") or "unclear")
        cap = (
            INTENT_CAPABILITY.get(key)
            or INTENT_CAPABILITY.get(str(intent.get("canonical")))
            or "clarify"
        )
        return {
            "capability": cap,
            "handler": CAPABILITY_HANDLERS.get(cap, _cap_clarify),
            "intent": key,
        }

    def execute(
        self,
        capability: dict[str, Any],
        question: str,
        context: dict[str, Any],
        understanding: dict[str, Any],
    ) -> str:
        fn = capability.get("handler") or _cap_clarify
        # Prefer tool results already executed by CognitiveIntelligence
        tool_text = ""
        if isinstance(context, dict):
            tool_text = str(context.get("tool_context") or "").strip()
            if not tool_text:
                tr = context.get("tool_results") or {}
                tool_text = str(tr.get("combined_text") or "").strip()

        out = str(fn(question, context, understanding) or "").strip()
        cap_id = str(capability.get("capability") or "")

        # Merge: if handler empty/weak but tools ran, use tools
        if tool_text and (not out or len(out) < 40):
            out = tool_text
        elif tool_text and out and tool_text[:80] not in out:
            # Enrich coding/research with tool evidence — not prompt_generator/chat
            if cap_id in {"coding", "research", "analysis", "planning"}:
                out = f"{out}\n\n## Tool results\n{tool_text}"

        if not out:
            return ""
        if not _static_ok() and looks_like_static_reply(out):
            # Still allow tool-backed content through
            if tool_text and not looks_like_static_reply(tool_text):
                return tool_text + "\n"
            return ""
        if "Produce production-quality output" in out and "Prefer TypeScript when building UI" in out:
            return (tool_text + "\n") if tool_text else ""
        if "Here’s a clear take" in out or ("Core idea" in out and "How it works" in out):
            return (tool_text + "\n") if tool_text else ""
        try:
            from om_ai.core.intelligence.real_answer import _looks_like_garbage

            cap_id = str(capability.get("capability") or "")
            if cap_id not in {"date", "calculator", "chat"} and _looks_like_garbage(out):
                if tool_text and not _looks_like_garbage(tool_text):
                    return tool_text + "\n"
                return ""
        except Exception:
            pass
        return out + "\n"
