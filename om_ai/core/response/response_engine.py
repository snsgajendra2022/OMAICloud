from __future__ import annotations

from typing import Any

from .answer_planner import AnswerPlanner
from .format_selector import FormatSelector
from .quality_checker import QualityChecker
from .improvement_engine import ImprovementEngine
from .response_state import ResponseState
from .self_critic import SelfCritic
from .context_filter import ContextFilter
from .response_memory import ResponseMemory


class ResponseEngine:

    def __init__(self):
        self.planner = AnswerPlanner()
        self.format_selector = FormatSelector()
        self.quality_checker = QualityChecker()
        self.improvement_engine = ImprovementEngine()
        self.self_critic = SelfCritic()
        self.context_filter = ContextFilter()
        self.response_memory = ResponseMemory()

    def prepare(
        self,
        *,
        message: str,
        intent: str = "general",
        understanding: Any = None,
        reasoning: Any = None,
        context: dict | None = None,
    ) -> ResponseState:
        context = context or {}
        state = ResponseState(
            user_message=message,
            intent=intent or "general",
            context=context,
        )

        state.response_type = self.format_selector.select(
            intent=state.intent,
            message=message,
        )

        state.plan = self.planner.plan(
            message=message,
            intent=state.intent,
            understanding=understanding,
            reasoning=reasoning,
        )

        # Research-aware plan steps
        research = str(context.get("research") or "").strip()
        citations = context.get("citations") or []
        if research or citations:
            if state.response_type == "direct":
                state.response_type = "research"
            research_steps = [
                "Acknowledge that current information was needed",
                "Summarize verified findings clearly",
                "Cite sources when available",
            ]
            # Prepend without duplicating
            for step in reversed(research_steps):
                if step not in state.plan:
                    state.plan.insert(0, step)

        return state

    def generation_instruction(
        self,
        state: ResponseState,
    ) -> str:
        plan = "\n".join(f"- {item}" for item in state.plan)
        research = str((state.context or {}).get("research") or "").strip()
        citations = (state.context or {}).get("citations") or []
        cite_lines = ""
        if citations:
            bits = []
            for c in citations[:6]:
                if isinstance(c, dict):
                    bits.append(
                        f"- [{c.get('id', '')}] {c.get('title', '')} — {c.get('url', '')}"
                    )
                else:
                    bits.append(f"- {c}")
            cite_lines = "\n".join(bits)

        research_block = ""
        if research or cite_lines:
            research_block = f"""
Research context available:
{research[:4000]}

Citations:
{cite_lines or "(none)"}

When research context is present:
- Prefer verified research over guesses.
- Mention that current information was researched.
- Include a short Sources section when citations exist.
""".strip()

        return f"""
You are generating the final OM response.

User request:
{state.user_message}

Detected intent:
{state.intent}

Response mode:
{state.response_type}

Response plan:
{plan}

{research_block}

Important:
- Answer the complete user request.
- Do not answer based on one keyword.
- Do not output internal routing metadata.
- Do not dump unrelated retrieved context.
- Do not expose tool traces unless explicitly requested.
- Do not output training examples, Question:/Answer: pairs, or .jsonl rows.
- Do not output meaningless random word salad.
- Use coherent natural language.
""".strip()

    def validate(
        self,
        *,
        state: ResponseState,
        response: str,
    ) -> ResponseState:
        state.draft = (response or "").strip()

        result = self.quality_checker.validate(
            response=state.draft,
            original_message=state.user_message,
        )

        state.quality_score = result["score"]
        state.issues = result["issues"]
        state.approved = result["approved"]
        state.regenerate = not state.approved

        if state.approved:
            state.final = state.draft

        return state

    def retry_instruction(
        self,
        state: ResponseState,
    ) -> str:
        return self.improvement_engine.build_retry_instruction(
            issues=state.issues,
            original_message=state.user_message,
        )

    def clean_context(self, context):
        return self.context_filter.clean(context)

    def critic_check(self, question, answer):
        return self.self_critic.review(question, answer)

    def format_research_answer(
        self,
        *,
        message: str,
        draft: str,
        research_summary: str = "",
        citations: list | None = None,
        freshness_signals: list | None = None,
    ) -> str:
        """Human-facing research answer with sources block."""
        text = (draft or "").strip()
        citations = citations or []
        signals = freshness_signals or []

        if not text and not research_summary and not citations:
            return ""

        # If model already included Sources, keep it.
        low = text.lower()
        already_sourced = "sources:" in low or "according to" in low

        parts: list[str] = []
        if signals or research_summary or citations:
            topic = "current information"
            if "react" in (message or "").lower():
                topic = "current React release information"
            parts.append(
                "I detected this requires current information."
            )
            parts.append("")
            parts.append(f"Researching {topic}...")
            parts.append("")

        if text and not already_sourced:
            parts.append("According to verified sources:")
            parts.append("")
            parts.append(text)
        elif text:
            parts.append(text)
        elif research_summary:
            # Snippet-only fallback when model is offline
            snippet = research_summary
            # Prefer first source body
            if "[SOURCE 1]" in snippet:
                body = snippet.split("[SOURCE 1]", 1)[-1]
                lines = [
                    ln
                    for ln in body.splitlines()
                    if ln.strip()
                    and not ln.startswith("Title:")
                    and not ln.startswith("URL:")
                    and not ln.startswith("Confidence:")
                    and not ln.startswith("[SOURCE")
                ]
                snippet = "\n".join(lines[:12]).strip()
            parts.append("According to verified sources:")
            parts.append("")
            parts.append(snippet[:1200])

        if citations and "sources:" not in low:
            parts.append("")
            parts.append("Sources:")
            for c in citations[:6]:
                if isinstance(c, dict):
                    title = c.get("title") or "Source"
                    url = c.get("url") or ""
                    parts.append(f"- {title}: {url}".strip())
                else:
                    parts.append(f"- {c}")

        return "\n".join(parts).strip()
