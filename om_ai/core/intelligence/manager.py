"""
Cognitive intelligence manager.

User → Understand → Think → Retrieve → Plan → Generate → Verify → Reply
"""
from __future__ import annotations

from typing import Any

from .understanding_engine import UnderstandingEngine
from .intent_engine import IntentEngine
from .context_manager import ContextManager
from .capability_router import CapabilityRouter
from .tool_planner import ToolPlanner
from .response_validator import ResponseValidator
from .self_correction import SelfCorrection


class CognitiveIntelligence:
    def __init__(self) -> None:
        self.understanding_engine = UnderstandingEngine()
        self.intent_engine = IntentEngine()
        self.context_manager = ContextManager()
        self.capability_router = CapabilityRouter()
        self.tool_planner = ToolPlanner()
        self.validator = ResponseValidator()
        self.correction = SelfCorrection()

    def run(
        self,
        question: str,
        *,
        messages: list[dict] | None = None,
        memory_context: dict | list | None = None,
        user_profile: dict | None = None,
        project: dict | str | None = None,
    ) -> dict[str, Any]:
        q = (question or "").strip()
        context = self.context_manager.load(
            q,
            messages=messages,
            memory_context=memory_context,
            user_profile=user_profile,
            project=project,
        )
        understanding = self.understanding_engine.understand(q, context=context)
        intent = self.intent_engine.resolve(understanding)
        capability = self.capability_router.route(intent)
        tools = self.tool_planner.plan(intent, capability, understanding)

        # Think / plan trace (internal)
        plan = {
            "stages": ["understand", "think", "retrieve", "plan", "generate", "verify", "reply"],
            "capability": capability.get("capability"),
            "tools": tools.get("tools"),
            "confidence": intent.get("confidence"),
        }

        answer = self.capability_router.execute(capability, q, context, understanding)
        validation = self.validator.validate(
            q,
            answer,
            understanding=understanding,
            intent=intent,
            capability=capability,
        )
        if not validation.get("passed"):
            answer = self.correction.correct(
                q,
                answer,
                validation,
                router=self.capability_router,
                capability=capability,
                context=context,
                understanding=understanding,
                intent=intent,
            )
            validation = self.validator.validate(
                q,
                answer,
                understanding=understanding,
                intent=intent,
                capability=capability,
            )

        # Absolute rules
        if self.validator._is_echo(q, answer):
            answer = self.capability_router.execute(
                self.capability_router.route({"intent": "unclear"}),
                q,
                context,
                understanding,
            )

        return {
            "question": q,
            "understanding": understanding,
            "intent": intent,
            "context": context,
            "capability": {
                "id": capability.get("capability"),
                "intent": capability.get("intent"),
            },
            "tools": tools,
            "plan": plan,
            "answer": answer if answer.endswith("\n") else answer + "\n",
            "validation": validation,
            "pipeline": plan["stages"],
        }


def run_cognitive_intelligence(question: str, **kwargs: Any) -> dict[str, Any]:
    return CognitiveIntelligence().run(question, **kwargs)
