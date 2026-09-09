"""
OM-1.0 Cognitive Brain — staged thinking pipeline.

Flow:

  message
    ↓
  Understanding
    ↓
  ReasoningEngine
    ↓
  CodingIntelligence
    ↓
  ResponseEngine
    ↓
  OM Native Model
    ↓
  QualityChecker
    ↓
  Answer

Usage:

  OMCognitiveBrain().process("create react native login and dashboard app")
  OMCognitiveBrain().generate("hello")
"""
from __future__ import annotations

from typing import Any, Callable

from om_ai.memory import MemoryManager
from om_ai.agents import AgentRouter, AgentExecutor
from om_ai.cognition.intent_engine import IntentEngine
from om_ai.learning import LearningEngine
from om_ai.reflection import ReflectionEngine
from om_ai.orchestration import OMOrchestrator
from om_ai.cognition.task_planner import TaskPlanner
from om_ai.evaluation.self_checker import SelfEvaluator
from om_ai.improvement import KnowledgeImprovementEngine
from om_ai.cognition.technology_engine import TechnologyEngine
from om_ai.core.reasoning.reasoning_chain import ReasoningChain
from om_ai.core.reasoning.reasoning_engine import ReasoningEngine
from om_ai.core.coding.coding_intelligence import CodingIntelligence
from om_ai.core.response.response_engine import ResponseEngine
from om_ai.core.response.quality_checker import QualityChecker
from om_ai.core.response.answer_generator import AnswerGenerator
from om_ai.memory_intelligence import MemoryConsolidator
from om_ai.user_intelligence import UserIntelligenceEngine
from om_ai.context import ContextEngine
from om_ai.understanding.query_kind import is_coding_task, is_greeting, query_kind
from om_ai.agents.collaboration import AgentCollaborationPlanner, AgentCoordinator


class OMCognitiveBrain:

    def __init__(self) -> None:
        self.memory = MemoryManager()
        self.intent = IntentEngine()
        self.technology = TechnologyEngine()
        self.planner = TaskPlanner()
        self.reasoning = ReasoningChain()
        self.reasoning_engine = ReasoningEngine()
        self.coding_intelligence = CodingIntelligence()
        self.response_engine = ResponseEngine()
        self.quality_checker = QualityChecker()
        self.generator = AnswerGenerator()
        self.evaluator = SelfEvaluator()
        self.agent_router = AgentRouter()
        self.agent_executor = AgentExecutor()
        self.agent_planner = AgentCollaborationPlanner()
        self.agent_coordinator = AgentCoordinator()
        self.learning = LearningEngine()
        self.improvement = KnowledgeImprovementEngine()
        self.orchestrator = OMOrchestrator()
        self.reflection_engine = ReflectionEngine()
        self.memory_consolidator = MemoryConsolidator()
        self.user_intelligence = UserIntelligenceEngine()
        self.context_engine = ContextEngine()

    def generate(
        self,
        message: str,
        *,
        knowledge: Any = None,
        memory: Any = None,
        native_chat: Callable[..., str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Core OM brain flow:

        message → Understanding → ReasoningEngine → CodingIntelligence
        → ResponseEngine → OM Native Model → QualityChecker → Answer
        """
        message = (message or "").strip()
        stages: list[str] = []
        meta: dict[str, Any] = {"flow": "om-brain-v2"}

        # 1) Understanding
        stages.append("understanding")
        understanding: dict[str, Any] = {}
        try:
            from om_ai.core.intelligence.understanding_engine import UnderstandingEngine

            understanding = UnderstandingEngine().understand(
                message,
                context=context or {},
            )
        except Exception as exc:
            understanding = {
                "intent": query_kind(message) if message else "chat",
                "action": "chat",
                "domain": "general",
                "confidence": 0.4,
                "error": str(exc),
            }
        intent_name = str(understanding.get("intent") or "chat")
        meta["understanding"] = {
            "intent": intent_name,
            "domain": understanding.get("domain"),
            "confidence": understanding.get("confidence"),
        }

        # 2) ReasoningEngine
        stages.append("reasoning")
        reasoning_out: dict[str, Any] = {}
        try:
            reasoning_out = self.reasoning_engine.process(message, message)
        except Exception as exc:
            reasoning_out = {"status": "error", "error": str(exc)}
        meta["reasoning"] = {
            "status": reasoning_out.get("status"),
            "plan": reasoning_out.get("plan"),
        }

        # 3) CodingIntelligence (coding asks only; else light stub)
        stages.append("coding_intelligence")
        coding_out: dict[str, Any] = {}
        if is_coding_task(message) or intent_name in {
            "coding",
            "debug",
            "architecture",
            "prompt_generation",
        }:
            try:
                coding_out = self.coding_intelligence.analyze(message)
            except Exception as exc:
                coding_out = {"error": str(exc)}
        meta["coding"] = {
            "used": bool(coding_out),
            "frameworks": (coding_out.get("requirement") or {}).get("framework")
            if isinstance(coding_out.get("requirement"), dict)
            else [],
        }

        # 4) ResponseEngine (plan + format)
        stages.append("response_engine")
        prepared: dict[str, Any] = {}
        try:
            prepared = self.response_engine.prepare(message, intent_name)
        except Exception as exc:
            prepared = {"plan": [], "response_type": "chat", "error": str(exc)}
        meta["response_plan"] = prepared

        # 5) OM Native Model
        stages.append("om_native_model")
        draft = self._native_or_fallback_answer(
            message,
            understanding=understanding,
            reasoning=reasoning_out,
            coding=coding_out,
            prepared=prepared,
            knowledge=knowledge,
            memory=memory,
            native_chat=native_chat,
        )
        meta["model"] = {"chars": len(draft or "")}

        # 6) QualityChecker
        stages.append("quality_checker")
        quality = self.quality_checker.validate(draft)
        if not quality.get("approved") and draft:
            repaired = self._repair_answer(message, draft, understanding)
            quality2 = self.quality_checker.validate(repaired)
            if quality2.get("approved") or len(repaired) > len(draft):
                draft = repaired
                quality = quality2
        meta["quality"] = quality

        # 7) Answer
        stages.append("answer")
        answer = (draft or "").strip()
        if not answer:
            answer = self._safe_fallback(message, intent_name)

        return {
            "answer": answer,
            "understanding": understanding,
            "reasoning": reasoning_out,
            "coding": coding_out,
            "response_plan": prepared,
            "quality": quality,
            "stages": stages,
            "meta": meta,
            "intent": understanding,
            "technology": {
                "frameworks": meta["coding"].get("frameworks") or [],
            },
        }

    def _native_or_fallback_answer(
        self,
        message: str,
        *,
        understanding: dict[str, Any],
        reasoning: dict[str, Any],
        coding: dict[str, Any],
        prepared: dict[str, Any],
        knowledge: Any,
        memory: Any,
        native_chat: Callable[..., str] | None,
    ) -> str:
        intent_name = str(understanding.get("intent") or "")
        if is_greeting(message) or intent_name == "conversation":
            low = message.lower()
            if "morning" in low or "moring" in low:
                return "Good morning! I’m OM — how can I help you today?"
            if "evening" in low:
                return "Good evening! I’m OM — how can I help you?"
            return "Hello — I’m OM. How can I help you?"

        if callable(native_chat):
            try:
                sys_bits = [
                    "You are OM, a helpful local AI assistant.",
                    f"Intent: {intent_name}",
                ]
                plan = reasoning.get("plan") or prepared.get("plan") or []
                if plan:
                    sys_bits.append("Plan: " + "; ".join(str(p) for p in plan[:6]))
                if coding:
                    req = coding.get("requirement") or {}
                    if req:
                        sys_bits.append(f"Coding context: {req}")
                messages = [
                    {"role": "system", "content": "\n".join(sys_bits)},
                    {"role": "user", "content": message},
                ]
                text = str(native_chat(messages) or "").strip()
                if text:
                    return text
            except Exception:
                pass

        try:
            from om_ai.backends.om_native import OmNativeBackend

            backend = None
            try:
                from om_ai.api import main as app_main

                backend = getattr(app_main, "native_backend", None)
            except Exception:
                backend = None
            if backend is None:
                backend = OmNativeBackend()
            if getattr(backend, "loaded", False) and callable(getattr(backend, "chat", None)):
                text = str(
                    backend.chat(
                        [
                            {
                                "role": "system",
                                "content": "You are OM. Answer clearly and helpfully.",
                            },
                            {"role": "user", "content": message},
                        ]
                    )
                    or ""
                ).strip()
                if text:
                    return text
        except Exception:
            pass

        try:
            # Prefer a clean structured draft from coding + response plan
            if coding and isinstance(coding, dict) and not coding.get("error"):
                req = coding.get("requirement") or {}
                arch = coding.get("architecture") or {}
                lines = [
                    "Here is a clear plan for your coding request.",
                    "",
                ]
                frameworks = req.get("framework") if isinstance(req, dict) else None
                features = req.get("features") if isinstance(req, dict) else None
                if frameworks:
                    lines.append("Stack: " + ", ".join(str(x) for x in frameworks))
                if features:
                    lines.append("Features: " + ", ".join(str(x) for x in features))
                if isinstance(arch, dict) and arch:
                    bits = []
                    for k, v in list(arch.items())[:8]:
                        if isinstance(v, (list, tuple)):
                            bits.append(f"{k}=" + ", ".join(str(x) for x in v))
                        else:
                            bits.append(f"{k}={v}")
                    if bits:
                        lines.append("Architecture: " + "; ".join(bits))
                elif arch:
                    lines.append(str(arch)[:800])
                plan = reasoning.get("plan") or prepared.get("plan") or []
                if plan:
                    lines.append("")
                    lines.append("Next steps:")
                    for i, step in enumerate(plan[:6], 1):
                        lines.append(f"{i}. {step}")
                text = "\n".join(lines).strip()
                if text:
                    return text

            generated = self.generator.generate(
                message,
                {
                    "memory_context": memory or [],
                    "plan": reasoning.get("plan") or prepared.get("plan") or [],
                    "analysis": reasoning.get("analysis") or {},
                    "coding": coding,
                    "understanding": understanding,
                },
                knowledge,
            )
            if isinstance(generated, dict):
                ans = str(generated.get("answer") or "").strip()
            else:
                ans = str(generated or "").strip()
            # Reject dumps that look like raw understanding schema
            low = ans.lower()
            if ans and not (
                low.startswith("intent:")
                or "confidence:" in low[:80]
                or low.startswith("tokens:")
            ):
                return ans
            return ""
        except Exception:
            return ""

    def _repair_answer(
        self,
        message: str,
        draft: str,
        understanding: dict[str, Any],
    ) -> str:
        intent_name = str(understanding.get("intent") or "chat")
        try:
            ok = self.response_engine.validate(draft)
            if ok.get("approved"):
                return draft
        except Exception:
            pass
        return self._safe_fallback(message, intent_name)

    def _safe_fallback(self, message: str, intent_name: str) -> str:
        if is_greeting(message) or intent_name == "conversation":
            return "Hello — I’m OM. How can I help you?"
        if is_coding_task(message):
            return (
                "I understood this as a coding request. "
                "Share the stack and the first feature you want, and I’ll outline a clear plan."
            )
        return (
            "I can help with that. Please share a bit more detail so I can give a precise answer."
        )

    def process(
        self,
        question: str,
        knowledge: Any = None,
        *,
        native_chat: Callable[..., str] | None = None,
    ) -> dict[str, Any]:

        question = (question or "").strip()

        intelligence_result: dict[str, Any] = {}
        try:
            from om_ai.core.intelligence import CognitiveIntelligence

            intelligence_result = CognitiveIntelligence().run(
                question,
                memory_context=None,
            )
        except Exception:
            try:
                from om_ai.intelligence import IntelligenceManager

                intelligence_result = IntelligenceManager().run(
                    question,
                    memory_context=None,
                    knowledge=knowledge,
                )
            except Exception:
                intelligence_result = {}

        agent_result = self.agent_router.route(question)
        existing_memory = self.memory.get_context()
        relevant_memory = self.memory.get_relevant_memory(
            question,
            memories=existing_memory,
        )
        memory_context = {"relevant": relevant_memory}
        context_result = self.context_engine.understand(
            question,
            user=self.user_intelligence.profile_data(),
            memory=memory_context,
        )
        orchestration = self.orchestrator.orchestrate(
            question,
            agent_result,
            memory=memory_context,
            knowledge=knowledge,
        )
        agent_plan = self.agent_planner.plan(question)
        agent_team_result = self.agent_coordinator.execute(
            agent_plan,
            question,
            {"memory": memory_context},
        )
        agent_execution = self.agent_executor.execute(
            agent_result,
            question,
            {"memory": memory_context},
        )

        if not question:
            return {
                "answer": "",
                "user_response": "",
                "developer_response": "",
                "agent": agent_result,
                "learning": {},
                "debug": {},
                "evaluation": {
                    "approved": False,
                    "score": 0,
                    "issues": ["empty question"],
                },
            }

        kind = query_kind(question)
        intent_result = self.intent.analyze(question)

        if is_coding_task(question):
            technology_result = self.technology.analyze(question)
        else:
            technology_result = {
                "technology": None,
                "category": "unknown",
                "language": None,
                "platform": None,
                "confidence": 0,
            }

        task_result = self.planner.decompose(question)
        if kind in {"greeting", "knowledge"}:
            task_result = {
                "goal": question,
                "category": "general",
                "tasks": [],
            }

        hits = None
        if kind == "greeting":
            hits = []
        elif isinstance(knowledge, list):
            hits = knowledge
        elif isinstance(knowledge, dict):
            hits = knowledge.get("hits") or knowledge.get("results") or []

        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

        pipeline = run_reasoning_pipeline(
            question,
            knowledge_hits=hits,
            retrieve=not hits and kind != "greeting",
            messages=None,
        )
        pipeline["agent"] = agent_result
        pipeline["agent_execution"] = agent_execution
        pipeline["agent_plan"] = agent_plan
        pipeline["agent_team"] = agent_team_result
        pipeline["orchestration"] = orchestration
        pipeline["intelligence"] = intelligence_result

        # Core flow: Understanding → Reasoning → Coding → Response
        # → Native Model → QualityChecker → Answer
        generated_flow = self.generate(
            question,
            knowledge=knowledge,
            memory=relevant_memory,
            native_chat=native_chat,
            context={
                "memory": memory_context,
                "agent": agent_result,
                "project_hint": "",
            },
        )
        user_answer = str(generated_flow.get("answer") or "").strip()

        intel_answer = str((intelligence_result or {}).get("answer") or "").strip()
        if intel_answer and len(intel_answer) > max(40, len(user_answer)):
            qcheck = self.quality_checker.validate(intel_answer)
            if qcheck.get("approved"):
                user_answer = intel_answer

        consolidated_memory = self.memory_consolidator.consolidate(
            {
                "type": "conversation",
                "content": {"question": question, "answer": user_answer},
            }
        )
        self.memory.remember_conversation(question, user_answer)
        user_profile = self.user_intelligence.learn(question)

        evaluation = pipeline.get("evaluation")
        reflection_result = self.reflection_engine.process(
            {
                "success": (evaluation or {}).get("approved", False)
                if isinstance(evaluation, dict)
                else False,
                "answer": user_answer,
            },
            evaluation or {},
        )
        if not evaluation:
            evaluation = self.evaluator.evaluate(
                question,
                user_answer,
                technology_result,
            )
        flow_quality = generated_flow.get("quality") or {}
        if isinstance(evaluation, dict) and flow_quality:
            evaluation = {
                **evaluation,
                "quality_checker": flow_quality,
                "approved": bool(
                    evaluation.get("approved", True) and flow_quality.get("approved", True)
                ),
            }

        improvement_result = self.improvement.improve(
            question,
            user_answer,
            evaluation,
        )
        learning_result = self.learning.learn(
            question,
            user_answer,
            evaluation,
        )

        from om_ai.core.response.response_formatter import (
            ResponseFormatter,
            response_mode,
        )

        formatter = ResponseFormatter()
        payload = {
            "question": question,
            "intent": generated_flow.get("understanding")
            or pipeline.get("intent")
            or intent_result,
            "technology": pipeline.get("technology") or technology_result,
            "tasks": task_result,
            "reasoning": {
                **(pipeline if isinstance(pipeline, dict) else {}),
                "brain_flow": generated_flow.get("reasoning"),
                "coding": generated_flow.get("coding"),
                "stages": generated_flow.get("stages"),
            },
            "answer": user_answer,
            "evaluation": evaluation,
            "memory": memory_context,
            "agent": agent_result,
            "learning": learning_result,
            "improvement": improvement_result,
            "orchestration": orchestration,
            "reflection": reflection_result,
            "memory_consolidation": consolidated_memory,
            "user_profile": user_profile,
            "context": context_result,
            "intelligence": intelligence_result,
            "dynamic_answer": (intelligence_result or {}).get("answer") or "",
            "brain_flow": generated_flow.get("meta") or {},
        }

        user_response = formatter.format_user_response(payload)
        developer_response = formatter.format_developer_response(payload)
        visible = (
            developer_response if response_mode() == "developer" else user_response
        )

        return {
            "answer": visible,
            "user_response": user_response,
            "developer_response": developer_response,
            "agent": agent_result,
            "memory": memory_context,
            "intent": payload["intent"],
            "technology": payload["technology"],
            "tasks": task_result,
            "reasoning": payload["reasoning"],
            "evaluation": evaluation,
            "learning": learning_result,
            "improvement": improvement_result,
            "orchestration": orchestration,
            "reflection": reflection_result,
            "stages": generated_flow.get("stages") or [],
            "brain_flow": generated_flow,
        }
