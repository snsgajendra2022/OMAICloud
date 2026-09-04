"""
Tool Decision Engine — decide IF tools are needed and WHICH ones.

Direct answers (explain Python) → no tools.
Live/action asks (weather, files, code run) → select tools.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolDecision:
    needs_tools: bool
    tools: list[str] = field(default_factory=list)
    reason: str = ""
    confidence: float = 0.5
    mode: str = "answer"  # answer | action | research | code | file | live
    risk: str = "low"  # low | medium | high


# Patterns that imply action / live data rather than pure explanation
_LIVE = re.compile(
    r"\b(weather|today'?s?\s+news|stock\s+price|current\s+(?:time|date)|"
    r"latest|live|right\s+now|as\s+of\s+today)\b",
    re.I,
)
_CALC = re.compile(
    r"(\d+\s*%\s*of\s*\d+)|(\d+\s*[\+\-\*\/]\s*\d+)|"
    r"\b(calculate|compute|how\s+much\s+is)\b",
    re.I,
)
_FILE = re.compile(
    r"\b(read\s+file|open\s+file|list\s+files?|show\s+(?:readme|package\.json)|"
    r"\.py\b|\.md\b|\.json\b|workspace|folder)\b",
    re.I,
)
_CODE = re.compile(
    r"\b(write\s+code|generate\s+code|implement|debug|fix\s+bug|"
    r"create\s+(?:a\s+)?(?:react|fastapi|django|laravel)|run\s+(?:this\s+)?(?:script|code))\b",
    re.I,
)
_WEB = re.compile(
    r"\b(search\s+(?:the\s+)?web|google|look\s+up\s+online|browse|"
    r"fetch\s+(?:url|page)|https?://)\b",
    re.I,
)
_DB = re.compile(
    r"\b(sql|sqlite|postgres|database\s+query|select\s+from)\b",
    re.I,
)
_SHELL = re.compile(
    r"\b(run\s+(?:command|shell|terminal)|bash|execute\s+command)\b",
    re.I,
)
_VISION = re.compile(
    r"\b(image|photo|diagram|screenshot|ocr|what\s+(?:do\s+you\s+)?see)\b",
    re.I,
)
_DATE = re.compile(
    r"\b(what(?:'s|\s+is)\s+(?:the\s+)?date|today'?s\s+date|current\s+date|"
    r"what\s+day\s+is\s+it)\b",
    re.I,
)
_SOCIAL_DAY = re.compile(
    r"\bhow\s+(was|is|are|'s)\s+(your\s+)?(day|date|night|evening|morning)\b|"
    r"^good\s+(morning|moring|evening|afternoon)\b",
    re.I,
)
_PURE_EXPLAIN = re.compile(
    r"^\s*(what\s+is|explain|define|describe|tell\s+me\s+about)\b",
    re.I,
)


class ToolDecisionEngine:
    """Decide tool use from question + optional intent/capability hints."""

    def decide(
        self,
        question: str,
        *,
        intent: dict[str, Any] | None = None,
        capability: dict[str, Any] | None = None,
        understanding: dict[str, Any] | None = None,
        has_attachment: bool = False,
    ) -> ToolDecision:
        q = (question or "").strip()
        intent = intent or {}
        capability = capability or {}
        understanding = understanding or {}

        # Tool Decision Layer — ContextIntentClassifier (not "date" in message)
        try:
            from om_ai.core.understanding.context_intent import classify_context_intent

            ctx = classify_context_intent(q)
            if ctx.get("intent") == "conversation" or (
                not ctx.get("use_tools") and ctx.get("intent") in {"general", "research"}
            ):
                return ToolDecision(
                    needs_tools=False,
                    tools=[],
                    reason=str(ctx.get("reason") or "context_classifier"),
                    confidence=0.95,
                    mode="answer",
                    risk="low",
                )
            if ctx.get("intent") == "date_query":
                return ToolDecision(
                    needs_tools=True,
                    tools=["date"],
                    reason="context_classifier:date_query",
                    confidence=0.95,
                    mode="live",
                    risk="low",
                )
            if ctx.get("intent") == "calculation":
                return ToolDecision(
                    needs_tools=True,
                    tools=["calculator"],
                    reason="context_classifier:calculation",
                    confidence=0.95,
                    mode="action",
                    risk="low",
                )
            if ctx.get("tools") and ctx.get("use_tools"):
                return ToolDecision(
                    needs_tools=True,
                    tools=list(ctx.get("tools") or []),
                    reason=str(ctx.get("reason") or "context_classifier"),
                    confidence=0.85,
                    mode="live" if "web" in (ctx.get("tools") or []) else "action",
                    risk="medium",
                )
        except Exception:
            pass

        # Social greetings / how was your day — never tools (check first)
        if _SOCIAL_DAY.search(q) and not _DATE.search(q):
            return ToolDecision(
                needs_tools=False,
                tools=[],
                reason="social_checkin",
                confidence=0.95,
                mode="answer",
                risk="low",
            )

        tools: list[str] = []
        reasons: list[str] = []
        mode = "answer"
        risk = "low"
        confidence = 0.55

        # Capability defaults from planner registry
        cap = str(capability.get("capability") or intent.get("intent") or "")
        try:
            from om_ai.core.intelligence.tool_planner import CAPABILITY_TOOLS

            tools.extend(CAPABILITY_TOOLS.get(cap, []))
            if tools:
                reasons.append(f"capability:{cap}")
                mode = "action" if tools else "answer"
        except Exception:
            pass

        if _DATE.search(q) and not _SOCIAL_DAY.search(q) and "date" not in tools:
            tools.append("date")
            reasons.append("date_request")
            mode = "live"
            confidence = 0.9

        if _CALC.search(q) and "calculator" not in tools:
            tools.append("calculator")
            reasons.append("calculation")
            mode = "action"
            risk = "low"
            confidence = 0.9
        # Pure arithmetic → calculator only (skip noisy knowledge)
        if _CALC.search(q) and not _CODE.search(q) and not _FILE.search(q):
            tools = ["calculator"] + [t for t in tools if t == "date"]
            reasons.append("calc_only")
            mode = "action"
            confidence = 0.95

        if _FILE.search(q) and "file" not in tools:
            tools.append("file")
            reasons.append("file_ops")
            mode = "file"
            risk = "medium"
            confidence = 0.85

        if _CODE.search(q):
            for t in ("code_execution", "knowledge", "file"):
                if t not in tools:
                    tools.append(t)
            reasons.append("coding")
            mode = "code"
            risk = "medium"
            confidence = 0.85

        if _WEB.search(q) or _LIVE.search(q):
            if "web" not in tools:
                tools.append("web")
            if "knowledge" not in tools:
                tools.append("knowledge")
            reasons.append("live_or_web")
            mode = "live"
            risk = "medium"
            confidence = 0.8

        if _DB.search(q) and "database" not in tools:
            tools.append("database")
            reasons.append("database")
            mode = "action"
            risk = "high"
            confidence = 0.75

        if _SHELL.search(q) and "terminal" not in tools:
            tools.append("terminal")
            reasons.append("shell")
            mode = "action"
            risk = "high"
            confidence = 0.8

        if has_attachment or _VISION.search(q):
            if "vision" not in tools:
                tools.append("vision")
            reasons.append("vision")
            mode = "action"
            confidence = 0.8

        # Pure explanation without action cues → drop tools (except knowledge for research intents)
        if (
            _PURE_EXPLAIN.match(q)
            and not any(
                [
                    _LIVE.search(q),
                    _CALC.search(q),
                    _FILE.search(q),
                    _CODE.search(q),
                    _WEB.search(q),
                    _SHELL.search(q),
                    _DATE.search(q),
                ]
            )
            and cap in {"", "chat", "explanation", "research", "question"}
        ):
            # Keep knowledge only for substantive research; skip live/action tools
            tools = [t for t in tools if t == "knowledge"]
            if "explain python" in q.lower() or re.match(
                r"^\s*(what\s+is|explain)\s+\w+\s*$", q, re.I
            ):
                tools = []
                reasons = ["direct_answer_no_tool"]
                mode = "answer"
                confidence = 0.9

        # Substantive research with no tools yet → knowledge
        if (
            not tools
            and len(q.split()) >= 4
            and str(intent.get("intent") or "")
            in {"research", "explanation", "question", "comparison", "recommendation"}
        ):
            tools = ["knowledge"]
            reasons.append("research_knowledge")
            mode = "research"
            confidence = 0.7

        # Deduplicate preserve order
        seen: set[str] = set()
        ordered: list[str] = []
        for t in tools:
            if t not in seen:
                seen.add(t)
                ordered.append(t)

        force = os.environ.get("OM_FORCE_TOOLS", "").strip()
        if force:
            ordered = [x.strip() for x in force.split(",") if x.strip()]
            reasons.append("OM_FORCE_TOOLS")
            mode = "action"

        needs = bool(ordered)
        return ToolDecision(
            needs_tools=needs,
            tools=ordered,
            reason="; ".join(reasons) or ("no_tools" if not needs else "planned"),
            confidence=confidence,
            mode=mode,
            risk=risk if needs else "low",
        )
