"""AgentBrain — single entry for chat: understand → intent → gather → hint/fallback."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from om_ai.agent.context import budget_hint, pack_messages_for_tiny_context
from om_ai.agent.executor import ExecutionBundle, execute_for_chat, format_system_hint
from om_ai.agent.intent import ChatIntent, classify_intent
from om_ai.agent.verifier import compose_fallback, verify_reply
from om_ai.understanding import UnderstandingResult, understand_message


def _env_flag(name: str, default: bool = True) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw not in {"0", "false", "no", "off"}


def _map_understanding_intent(u: UnderstandingResult) -> ChatIntent:
    mapping = {
        "greeting": ChatIntent.greeting,
        "identity": ChatIntent.identity,
        "memory": ChatIntent.memory,
        "knowledge": ChatIntent.knowledge,
        "coding": ChatIntent.coding,
        "debugging": ChatIntent.coding,
        "planning": ChatIntent.agent,
        "completion": ChatIntent.agent,
        "understanding_feature": ChatIntent.agent,
        "ui_design": ChatIntent.agent,
    }
    return mapping.get(u.intent, classify_intent(u.corrected or u.original))


@dataclass
class AgentDecision:
    intent: ChatIntent
    packed_messages: list[dict[str, str]]
    extra_system: str = ""
    prefer_grounded: str = ""
    structured_fallback: str = ""
    understanding: UnderstandingResult | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def after_model(self, model_text: str | None) -> str | None:
        """If model output fails verification, return structured fallback (or None)."""
        fail = verify_reply(model_text, intent=self.intent.value)
        if not fail:
            # Optionally prepend public understanding line if model skipped it.
            u = self.understanding
            if (
                u
                and u.public_understanding
                and u.confidence >= 0.85
                and model_text
                and "understanding:" not in model_text.lower()
                and u.intent not in {"greeting", "identity"}
            ):
                # Keep model reply; only rescue on failure.
                return None
            return None
        if self.prefer_grounded:
            return self.prefer_grounded
        if self.structured_fallback:
            return self.structured_fallback
        return None


class AgentBrain:
    """ChatGPT-style assistant controller for OM (self-owned, no external LLM)."""

    def prepare(
        self,
        messages: list[dict[str, Any]],
        *,
        tenant_id: str = "default",
        actor: str = "",
        project_id: str | None = None,
        project_instructions: str = "",
    ) -> AgentDecision:
        if not _env_flag("OM_AGENT_BRAIN", True):
            user = ""
            for m in reversed(messages or []):
                if str(m.get("role") or "") == "user":
                    user = str(m.get("content") or "")
                    break
            return AgentDecision(
                intent=ChatIntent.chat,
                packed_messages=pack_messages_for_tiny_context(messages),
                meta={"disabled": True, "user": user[:80]},
            )

        user_text = ""
        for m in reversed(messages or []):
            if str(m.get("role") or "") == "user":
                user_text = str(m.get("content") or "").strip()
                break

        understanding = understand_message(
            user_text,
            messages=messages,
            project_instructions=project_instructions,
        )
        work_text = understanding.corrected or user_text
        intent = _map_understanding_intent(understanding)
        # Prefer agent intent classifier when understanding is low-confidence chat.
        if understanding.confidence < 0.65 and intent == ChatIntent.chat:
            intent = classify_intent(work_text)

        packed = pack_messages_for_tiny_context(messages)

        # Greetings / identity: light path, but still provide warm fallbacks.
        if intent in {ChatIntent.greeting, ChatIntent.identity}:
            return AgentDecision(
                intent=intent,
                packed_messages=packed,
                understanding=understanding,
                structured_fallback=compose_fallback(
                    intent=intent.value,
                    user_text=work_text,
                ),
                meta={"mode": "passthrough", "understanding": understanding.to_dict()},
            )

        bundle: ExecutionBundle = execute_for_chat(
            work_text,
            intent=intent.value,
            messages=messages,
            tenant_id=tenant_id,
            actor=actor,
            project_id=project_id,
        )
        hint_parts = []
        if understanding.system_hint:
            # Budget for tiny OM windows.
            uh = understanding.system_hint.strip()
            if len(uh) > 220:
                uh = uh[:217] + "..."
            hint_parts.append(uh)
        agent_hint = format_system_hint(bundle)
        if agent_hint:
            hint_parts.append(agent_hint)
        hint = budget_hint("\n".join(hint_parts), max_chars=260)

        fallback = compose_fallback(
            intent=intent.value,
            user_text=work_text,
            plan_bullets=bundle.plan_bullets or understanding.plan_steps,
            knowledge_snippets=bundle.knowledge_snippets,
            grounded_reply=bundle.grounded_reply,
        )
        # Cognitive layer fallback: lead with understood meaning for messy messages.
        if (
            understanding.public_understanding
            and understanding.confidence >= 0.8
            and (
                understanding.meta.get("tokens_changed")
                or understanding.intent in {"understanding_feature", "completion", "planning"}
            )
        ):
            solution = fallback or (
                "Solution: Use OM's understanding → intent → plan → reply pipeline "
                "so messy messages still get a correct answer."
            )
            if understanding.intent == "understanding_feature":
                solution = (
                    "Solution: Add / use the Cognitive Understanding Layer "
                    "(typo correction → intent → meaning → plan → verify) "
                    "before generating the final reply."
                )
            fallback = (
                f"{understanding.public_understanding}\n\n{solution}"
            ).strip()

        return AgentDecision(
            intent=intent,
            packed_messages=packed,
            extra_system=hint,
            prefer_grounded=bundle.grounded_reply,
            structured_fallback=fallback,
            understanding=understanding,
            meta={
                "mode": "agent",
                "notes": bundle.notes,
                "knowledge_hits": len(bundle.knowledge_snippets),
                "memory_hits": len(bundle.memory_snippets),
                "plan_steps": len(bundle.plan_bullets or understanding.plan_steps),
                "understanding": {
                    "intent": understanding.intent,
                    "confidence": understanding.confidence,
                    "goal": understanding.goal,
                    "corrected": understanding.corrected[:120],
                },
            },
        )
