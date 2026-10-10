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


def _native_synthesize(
    question: str,
    capability: str,
    context: dict[str, Any],
    understanding: dict[str, Any],
    *,
    tool_text: str = "",
    draft: str = "",
) -> str:
    """Generate the user-facing answer with OM's own checkpoint, not a canned template.

    The native checkpoint is the author of the answer. Retrieved facts, tool output,
    project context, and handler drafts are evidence only. If native inference is
    unavailable or the result looks like a static stub, return empty and let the
    caller make the failure explicit rather than silently substituting another LLM.
    """
    if os.environ.get("OM_CAPABILITY_NATIVE_GENERATION", "1").strip().lower() in {
        "0", "false", "no", "off"
    }:
        return ""

    from om_ai.backends.om_native import OMNativeBackend
    from om_ai.core.intelligence.real_answer import _looks_like_garbage

    task_instructions = {
        "coding": "Solve the coding task. Give complete, runnable code for requested files, explain important integration details, and never invent files or APIs.",
        "research": "Answer the question directly. Separate established facts from uncertainty and use supplied evidence rather than inventing citations.",
        "analysis": "Compare the relevant options using explicit criteria and reach a reasoned conclusion.",
        "planning": "Produce an executable plan with concrete actions, dependencies, and acceptance checks.",
        "recommendation": "Recommend a specific option for the user's stated needs and explain the trade-offs.",
        "prompt_generator": "Write a detailed, tailored prompt that can be used immediately for the exact task requested. Do not return a generic prompt skeleton.",
        "vision": "Answer only from the supplied image-analysis evidence. If evidence is missing, say the image analysis is unavailable.",
        "chat": "Respond naturally to the conversation, using prior turns when relevant. Do not restart the conversation or give a generic help menu.",
        "clarify": "Try to answer the user's likely intent. Ask one focused clarification only if an essential detail is missing.",
    }.get(capability, "Solve the user's request directly and concretely.")

    project_context = str(
        context.get("project_instructions")
        or context.get("project_hint")
        or context.get("project_context")
        or ""
    ).strip()
    history = context.get("history") or context.get("messages") or []
    # Short-turn conversation must not be buried under a long developer prompt.
    # The local OM model has a small context window; keep system instructions compact,
    # especially for greetings and multilingual casual conversation.
    short_chat = capability in {"chat", "clarify"} and len(question.strip()) <= 240 and not tool_text and not project_context
    if short_chat:
        system_prompt = (
            "You are OM, a friendly conversational AI. Reply directly and naturally to "
            "the user's latest message. Understand English and Hindi/Hinglish. Keep a "
            "greeting or simple social reply to one or two sentences. Do not give a menu "
            "of capabilities, repeat the question, or invent a refusal."
        )
    else:
        system_prompt = (
            "You are OM, using OM's own native model weights. Answer the user's request "
            "directly and concretely. Avoid canned headings and filler. Use supplied "
            "evidence; do not invent facts or claim tools ran without results. "
            + task_instructions
        )
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if isinstance(history, list):
        recent_history = history[-2:] if short_chat else history[-6:]
        for item in recent_history:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").lower()
            text = str(item.get("content") or "").strip()
            if role in {"user", "assistant"} and text:
                messages.append({"role": role, "content": text[:300] if short_chat else text[:1800]})
    evidence_parts = []
    if project_context:
        evidence_parts.append("PROJECT CONTEXT (follow when relevant):\n" + project_context[:5000])
    if tool_text:
        evidence_parts.append("EXECUTED TOOL RESULTS / EVIDENCE:\n" + tool_text[:10000])
    if draft:
        evidence_parts.append(
            "EXISTING SOLUTION DRAFT (verify and improve; do not copy blindly):\n" + draft[:6000]
        )
    if understanding:
        safe_understanding = {
            k: understanding[k]
            for k in ("intent", "canonical", "confidence", "entities", "constraints")
            if k in understanding
        }
        if safe_understanding:
            evidence_parts.append("INTENT METADATA:\n" + repr(safe_understanding)[:1800])
    user_content = question.strip()
    if evidence_parts:
        user_content += "\n\n" + "\n\n".join(evidence_parts)
    messages.append({"role": "user", "content": user_content})

    max_tokens = int(os.environ.get("OM_CAPABILITY_MAX_NEW_TOKENS", "768"))
    max_tokens = max(64, min(max_tokens, 2048))
    if short_chat:
        max_tokens = min(max_tokens, 64)
    answer = OMNativeBackend().chat(
        messages,
        max_new_tokens=max_tokens,
        temperature=0.7 if short_chat else 0.35,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.08 if short_chat else 1.12,
        min_new_tokens=1 if short_chat else 8,
        no_repeat_ngram_size=2 if short_chat else 3,
    )
    answer = str(answer or "").strip()
    if not answer or looks_like_static_reply(answer) or _looks_like_garbage(answer):
        return ""
    return answer


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

        cap_id = str(capability.get("capability") or "")
        native_generation = os.environ.get("OM_CAPABILITY_NATIVE_GENERATION", "1").strip().lower() not in {
            "0", "false", "no", "off"
        }
        # Keep deterministic tools and image analysis. Do not call build_real_answer
        # first for ordinary text tasks: that can invoke the same tiny model twice or
        # return a canned retrieval/template before native synthesis.
        if not native_generation or cap_id in {"date", "calculator", "vision", "coding"}:
            out = str(fn(question, context, understanding) or "").strip()
        else:
            out = ""

        # Clock and arithmetic are exact deterministic operations, not language generation.
        # Every other capability is synthesized by OM's native checkpoint first.
        if cap_id not in {"date", "calculator"}:
            try:
                native_answer = _native_synthesize(
                    question,
                    cap_id,
                    context if isinstance(context, dict) else {},
                    understanding if isinstance(understanding, dict) else {},
                    tool_text=tool_text,
                    draft=out,
                )
                if native_answer:
                    return native_answer + "\n"
            except Exception as exc:
                logger_name = "om_ai.core.intelligence.capability_router"
                import logging
                logging.getLogger(logger_name).warning(
                    "Native OM capability generation failed (%s); no third-party model fallback is used.",
                    type(exc).__name__,
                )
            # Do not silently ship a canned capability template as if OM generated it.
            if not tool_text.strip():
                return (
                    "OM's native model could not produce a usable answer. "
                    "Check that the configured OM checkpoint and tokenizer load correctly, "
                    "then inspect the native generation logs."
                )

        # Exact tool output is still useful if native synthesis is unavailable.
        if tool_text and (not out or len(out) < 40):
            out = tool_text
        elif tool_text and out and tool_text[:80] not in out:
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
