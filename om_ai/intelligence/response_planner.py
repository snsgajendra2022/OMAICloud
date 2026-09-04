"""Plan response style, then draft ONLY from real knowledge / reasoning / model."""
from __future__ import annotations

from typing import Any

from om_ai.core.intelligence.real_answer import build_real_answer, looks_like_static_reply


class ResponsePlanner:
    def plan_style(self, understanding: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
        complexity = str(understanding.get("complexity") or "medium")
        intent_name = str(intent.get("intent") or "")
        domain = str(understanding.get("domain") or "general")
        action = str(understanding.get("required_action") or "")

        if intent_name in {"chat"} or (complexity == "low" and action in {"chat", "answer"}):
            style = "short"
        elif domain in {"software", "architecture", "data"} and action in {
            "generate",
            "create",
            "debug",
        }:
            style = "technical_code"
        elif domain == "business" or action in {"plan", "analyze"}:
            style = "strategy"
        elif action in {"explain", "research", "summarize"} or domain == "science":
            style = "detailed"
        elif action == "recommend" or domain == "music":
            style = "recommendations"
        else:
            style = "balanced"

        return {
            "style": style,
            "tone": "helpful_direct",
            "ask_followup": style in {"recommendations", "technical_code", "strategy"},
        }

    def draft(
        self,
        question: str,
        understanding: dict[str, Any],
        intent: dict[str, Any],
        style: dict[str, Any],
        *,
        knowledge: dict[str, Any] | None = None,
        memory: dict[str, Any] | None = None,
        agents: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Real answer only — empty string means defer (no canned outline)."""
        packets = (knowledge or {}).get("packets") or []
        for p in packets:
            if p.get("source") == "facts" and p.get("texts"):
                t = str(p["texts"][0]).strip()
                if t and not looks_like_static_reply(t):
                    return t + "\n"
            if p.get("source") == "calendar_clock" and p.get("texts"):
                return str(p["texts"][0]).strip() + "\n"

        q = (question or "").strip()
        intent_name = str(intent.get("intent") or "")
        style_name = style.get("style") or "balanced"

        # Short greetings only
        qlow = q.lower()
        if intent_name == "chat" or style_name == "short":
            if qlow in {"hi", "hello", "hey", "yo", "sup"} or len(q.split()) <= 2 and qlow in {
                "hi",
                "hello",
                "hey",
            }:
                return "Hello — I'm OM. What would you like to work on?\n"

        prefer_coding = style_name == "technical_code" or intent_name in {
            "create",
            "code",
            "debug",
            "coding",
            "generate",
        } or any(
            w in qlow
            for w in ("code", "react", "python", "implement", "function", "api", "bug")
        )

        real = build_real_answer(
            q,
            prefer_coding=prefer_coding,
            knowledge_packets=list(packets),
        )
        if real:
            return real.strip() + "\n"
        # Memory snippets as last soft hint (must be substantial)
        for key in ("snippets", "hits", "items"):
            for s in (memory or {}).get(key) or []:
                t = str(s).strip() if not isinstance(s, dict) else str(s.get("text") or "").strip()
                if len(t) > 80 and not looks_like_static_reply(t):
                    return t + "\n"
        return ""
