"""Orchestrates the dynamic intelligence pipeline."""
from __future__ import annotations

from typing import Any

from .understanding_engine import UnderstandingEngine
from .intent_reasoner import IntentReasoner
from .context_engine import ContextEngine
from .memory_retriever import MemoryRetriever
from .knowledge_router import KnowledgeRouter
from .agent_selector import AgentSelector
from .tool_selector import ToolSelector
from .reasoning_engine import ReasoningEngine
from .response_planner import ResponsePlanner
from .quality_evaluator import QualityEvaluator


class IntelligenceManager:
    """
    Question → Understand → Think → Memory → Knowledge → Capability → Generate → Verify → Answer

    Regex/signals are helpers inside UnderstandingEngine only — they do not pick the final answer.
    """

    def __init__(self) -> None:
        self.understanding = UnderstandingEngine()
        self.intent_reasoner = IntentReasoner()
        self.context_engine = ContextEngine()
        self.memory = MemoryRetriever()
        self.knowledge = KnowledgeRouter()
        self.agents = AgentSelector()
        self.tools = ToolSelector()
        self.reasoning = ReasoningEngine()
        self.planner = ResponsePlanner()
        self.evaluator = QualityEvaluator()

    def run(
        self,
        question: str,
        *,
        messages: list[dict] | None = None,
        memory_context: dict | list | None = None,
        knowledge: Any = None,
        user_profile: dict | None = None,
        project: dict | str | None = None,
    ) -> dict[str, Any]:
        q = (question or "").strip()
        context = self.context_engine.build(
            q,
            messages=messages,
            memory=memory_context,
            user_profile=user_profile,
            project=project,
        )
        understanding = self.understanding.understand(q, context=context)
        intent = self.intent_reasoner.reason(understanding)
        memory_hits = self.memory.retrieve(
            q,
            conversation=context.get("history"),
            project=context.get("project_hint"),
            knowledge=knowledge,
            memory_context=memory_context,
        )
        knowledge_pack = self.knowledge.route(understanding, memory_hits=memory_hits)
        agents = self.agents.select(intent, understanding, context=context)
        tools = self.tools.select(understanding, intent, knowledge=knowledge_pack)
        # Execute selected tools (previously only stored as metadata)
        tool_out: dict[str, Any] = {}
        try:
            from om_ai.tools.chat_runner import execute_planned_tools, format_tool_context

            tool_out = execute_planned_tools(
                list(tools.get("tools") or []),
                q,
                context={**(context if isinstance(context, dict) else {}), "tenant_id": "default"},
            )
            if isinstance(context, dict):
                context["tool_results"] = tool_out
                context["tool_context"] = format_tool_context(tool_out)
            # Inject tool text into knowledge packets for the planner
            if tool_out.get("combined_text"):
                packets = list((knowledge_pack or {}).get("packets") or [])
                packets.insert(
                    0,
                    {
                        "source": "tools",
                        "texts": [str(tool_out["combined_text"])[:4000]],
                    },
                )
                knowledge_pack = {**(knowledge_pack or {}), "packets": packets}
        except Exception:
            tool_out = {"skipped": True}

        reason_plan = self.reasoning.plan(
            understanding,
            intent,
            agents=agents,
            tools=tools,
            knowledge=knowledge_pack,
            memory=memory_hits,
            context=context,
        )
        style = self.planner.plan_style(understanding, intent)
        answer = self.planner.draft(
            q,
            understanding,
            intent,
            style,
            knowledge=knowledge_pack,
            memory=memory_hits,
            agents=agents,
            context=context,
        )
        if not (answer or "").strip() and tool_out.get("combined_text"):
            answer = str(tool_out["combined_text"]).strip() + "\n"
        if isinstance(tools, dict):
            tools = {**tools, "executed": tool_out.get("executed") or [], "ok": bool(tool_out.get("ok"))}
        if not (answer or "").strip():
            return {
                "question": q,
                "understanding": understanding,
                "intent": intent,
                "context": context,
                "memory": memory_hits,
                "knowledge": knowledge_pack,
                "agents": agents,
                "tools": tools,
                "reasoning": reason_plan,
                "style": style,
                "answer": "",
                "evaluation": {"passed": False, "score": 0.0, "deferred": True},
                "deferred": True,
                "pipeline": [
                    "understand",
                    "intent",
                    "context",
                    "memory",
                    "knowledge",
                    "agents",
                    "tools",
                    "reason",
                    "generate",
                    "verify",
                ],
            }
        evaluation = self.evaluator.evaluate(
            q, answer, intent=intent, understanding=understanding
        )
        if evaluation.get("needs_regenerate"):
            answer = self.evaluator.regenerate(
                q,
                answer,
                evaluation,
                self.planner,
                understanding=understanding,
                intent=intent,
                knowledge=knowledge_pack,
                memory=memory_hits,
                agents=agents,
                context=context,
            )
            evaluation = self.evaluator.evaluate(
                q, answer, intent=intent, understanding=understanding
            )

        return {
            "question": q,
            "understanding": understanding,
            "intent": intent,
            "context": context,
            "memory": memory_hits,
            "knowledge": knowledge_pack,
            "agents": agents,
            "tools": tools,
            "reasoning": reason_plan,
            "style": style,
            "answer": (answer or "").strip() + ("\n" if answer and not str(answer).endswith("\n") else ""),
            "evaluation": evaluation,
            "pipeline": [
                "understand",
                "intent",
                "context",
                "memory",
                "knowledge",
                "agents",
                "tools",
                "reason",
                "generate",
                "verify",
            ],
        }


def run_intelligence(question: str, **kwargs: Any) -> dict[str, Any]:
    return IntelligenceManager().run(question, **kwargs)
