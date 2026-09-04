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

        # EXECUTE planned tools (was previously skipped — only stored in meta)
        tool_out: dict[str, Any] = {}
        try:
            from om_ai.tools.chat_runner import execute_planned_tools, format_tool_context

            tool_out = execute_planned_tools(
                list(tools.get("tools") or []),
                q,
                context={
                    **(context if isinstance(context, dict) else {}),
                    "tenant_id": str(
                        (context or {}).get("tenant_id")
                        if isinstance(context, dict)
                        else "default"
                    ),
                    "project_root": ".",
                },
            )
            if isinstance(context, dict):
                context["tool_results"] = tool_out
                context["tool_context"] = format_tool_context(tool_out)
        except Exception:
            tool_out = {"skipped": True, "executed": [], "ok": False}

        # Think / plan trace (internal)
        plan = {
            "stages": [
                "understand",
                "think",
                "retrieve",
                "plan",
                "tools",
                "generate",
                "verify",
                "reply",
            ],
            "capability": capability.get("capability"),
            "tools": tools.get("tools"),
            "tools_executed": tool_out.get("executed") or [],
            "tools_ok": bool(tool_out.get("ok")),
            "confidence": intent.get("confidence"),
        }

        answer = self.capability_router.execute(capability, q, context, understanding)
        # If capability empty but tools produced content — use tool output
        if not (answer or "").strip() and tool_out.get("combined_text"):
            answer = str(tool_out["combined_text"]).strip() + "\n"
        # Empty / static-deferred → do not pretend we answered (chat falls through)
        if not (answer or "").strip():
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
                "answer": "",
                "validation": {
                    "passed": False,
                    "score": 0.0,
                    "issues": ["no real answer from capability"],
                    "deferred": True,
                },
                "pipeline": plan["stages"],
                "deferred": True,
            }

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
            if not (answer or "").strip():
                validation = {
                    "passed": False,
                    "score": 0.0,
                    "issues": ["correction empty"],
                    "deferred": True,
                }
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
                    "answer": "",
                    "validation": validation,
                    "pipeline": plan["stages"],
                    "deferred": True,
                }
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
            if not (answer or "").strip():
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
                    "answer": "",
                    "validation": {"passed": False, "score": 0.0, "deferred": True},
                    "pipeline": plan["stages"],
                    "deferred": True,
                }

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
