"""Plan response style dynamically, then draft an answer from capabilities."""
from __future__ import annotations

from typing import Any


class ResponsePlanner:
    def plan_style(self, understanding: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
        complexity = str(understanding.get("complexity") or "medium")
        intent_name = str(intent.get("intent") or "")
        domain = str(understanding.get("domain") or "general")
        action = str(understanding.get("required_action") or "")

        if intent_name in {"chat"} or (complexity == "low" and action in {"chat", "answer"}):
            style = "short"
        elif domain in {"software", "architecture", "data"} and action in {"generate", "create", "debug"}:
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
        """Capability-driven draft — not per-topic static handlers."""
        # Prefer factual packets when present
        packets = (knowledge or {}).get("packets") or []
        for p in packets:
            if p.get("source") == "facts" and p.get("texts"):
                return str(p["texts"][0]).strip() + "\n"
            if p.get("source") == "calendar_clock" and p.get("texts"):
                return str(p["texts"][0]).strip() + "\n"

        style_name = style.get("style") or "balanced"
        domain = understanding.get("domain") or "general"
        goal = understanding.get("goal") or question
        team = (agents or {}).get("team") or ["general"]
        interp = (context or {}).get("interpretation") or ""

        if style_name == "short" or intent.get("intent") == "chat":
            return "Hello — I'm OM. What would you like to work on?\n"

        if style_name == "recommendations":
            return self._recommendations(question, domain)

        if style_name == "technical_code":
            return self._technical(question, goal, team, interp)

        if style_name == "strategy":
            return self._strategy(question, goal)

        if style_name == "detailed":
            return self._detailed(question, goal, packets)

        return self._balanced(question, goal, packets, interp)

    def _recommendations(self, question: str, domain: str) -> str:
        # Domain-shaped recommendation skeleton (expandable), not MusicAgent
        if domain == "music" or "playlist" in question.lower() or "music" in question.lower():
            return (
                "Here are playlist ideas:\n\n"
                "**Coding**\n"
                "- Deep Focus\n"
                "- Lo-Fi Beats\n\n"
                "**Workout**\n"
                "- Energy Boost\n\n"
                "**Relax**\n"
                "- Calm Evening\n\n"
                "Want a mood or genre to refine this?\n"
            )
        return (
            f"Here are practical suggestions for your request:\n\n"
            f"1. Clarify the outcome you want from: {question.strip()[:120]}\n"
            f"2. Pick constraints (time, budget, tools).\n"
            f"3. I can then produce a concrete shortlist.\n\n"
            f"What preference should I optimize for?\n"
        )

    def _technical(self, question: str, goal: str, team: list, interp: str) -> str:
        q = question.strip()
        low = q.lower()
        lines = [
            f"I'll treat this as: **{goal}**.",
            "",
        ]
        if interp:
            lines.extend([interp, ""])
        if "prompt" in low:
            lines.extend(
                [
                    "## Prompt",
                    "",
                    "You are an expert React engineer. Build a production-ready React application.",
                    "",
                    "Requirements:",
                    "- Clear folder structure (components, hooks, pages, services)",
                    "- TypeScript preferred",
                    "- Accessible UI and responsive layout",
                    "- State management approach explained",
                    "- Tests for critical flows",
                    "",
                    "Deliverables:",
                    "1. Architecture overview",
                    "2. File tree",
                    "3. Key code samples",
                    "4. Run / test instructions",
                    "",
                ]
            )
            if any(x in low for x in ("om", "cursor")):
                lines.extend(
                    [
                        "Context: optimize for Cursor / OM AI development workflows.",
                        "",
                    ]
                )
        else:
            lines.extend(
                [
                    "## Approach",
                    "",
                    "1. Clarify requirements and acceptance criteria",
                    "2. Choose stack / structure",
                    "3. Implement core path first",
                    "4. Add validation and tests",
                    "",
                    f"Suggested agents: {', '.join(team)}",
                    "",
                    "Tell me constraints (framework, auth, DB) and I will produce concrete code next.",
                    "",
                ]
            )
        return "\n".join(lines)

    def _strategy(self, question: str, goal: str) -> str:
        return (
            f"**Goal:** {goal}\n\n"
            "## Strategy\n\n"
            "1. Define success metrics\n"
            "2. Map current state vs desired state\n"
            "3. Prioritize highest-leverage actions\n"
            "4. Set a 7-day execution plan\n\n"
            f"Request: {question.strip()[:200]}\n\n"
            "Share constraints (budget, team size, timeline) for a tighter plan.\n"
        )

    def _detailed(self, question: str, goal: str, packets: list) -> str:
        extra = ""
        for p in packets:
            texts = p.get("texts") or []
            if texts:
                extra = "\n\n" + "\n".join(str(t) for t in texts[:2])
                break
        return (
            f"**Understanding:** {goal}\n\n"
            f"Here is a clear explanation for: {question.strip()}\n\n"
            "Core idea → how it works → why it matters → practical takeaway.\n"
            f"{extra}\n"
            "Want a deeper dive or a beginner version?\n"
        ).strip() + "\n"

    def _balanced(self, question: str, goal: str, packets: list, interp: str) -> str:
        bits = []
        for p in packets:
            for t in p.get("texts") or []:
                bits.append(str(t))
        body = "\n".join(bits[:3])
        if body:
            return body.strip() + "\n"
        prefix = (interp + "\n\n") if interp else ""
        return (
            f"{prefix}"
            f"I understand you want: **{goal}**.\n\n"
            f"Here's a direct path for “{question.strip()[:160]}”:\n"
            f"1. Restate the outcome\n"
            f"2. Break it into actionable steps\n"
            f"3. Deliver the first useful artifact\n\n"
            f"What should I produce first — outline, draft, or full solution?\n"
        )
