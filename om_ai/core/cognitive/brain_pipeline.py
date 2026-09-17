"""
OM-1.0 Cognitive Brain — STEPs 83–93 roadmap orchestration.

Flow:

  USER MESSAGE
        ↓
  Language Detection
        ↓
  Intent Understanding
        ↓
  Freshness Analysis → Research Engine (when needed)
        ↓
  Context Intelligence (memory + knowledge + research)
        ↓
  Reasoning Engine
        ↓
  Coding Intelligence
        ↓
  Response Planning
        ↓
  Intelligent Prompt → OM Native Model
        ↓
  Leakage → Garbage → Self Critic → Quality
        ↓
  Regeneration (max 2)
        ↓
  FINAL HUMAN ANSWER

Usage:

  OMCognitiveBrain().process("What is the latest React version?")
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
from om_ai.core.response.self_critic import SelfCritic
from om_ai.core.response.context_filter import ContextFilter
from om_ai.core.response.response_memory import ResponseMemory
from om_ai.core.response.answer_generator import AnswerGenerator
from om_ai.core.response.garbage_detector import GarbageDetector
from om_ai.core.response.tool_filter import ToolOutputFilter
from om_ai.core.response.leakage_detector import LeakageDetector
from om_ai.core.intelligence.freshness_detector import FreshnessDetector
from om_ai.core.context.context_intelligence import ContextIntelligence
from om_ai.core.research import ResearchEngine
from om_ai.core.steps import OMRoadmapStack
from om_ai.memory_intelligence import MemoryConsolidator
from om_ai.user_intelligence import UserIntelligenceEngine
from om_ai.context import ContextEngine
from om_ai.understanding.query_kind import is_coding_task, is_greeting, query_kind
from om_ai.understanding.language_brain import detect_language
from om_ai.agents.collaboration import AgentCollaborationPlanner, AgentCoordinator
from om_ai.core.knowledge_brain import KnowledgeBrain
from om_ai.core.research_intelligence import ResearchPipeline
from om_ai.core.long_context import LongContextEngine
from om_ai.core.advanced_reasoning import AdvancedReasoningEngine
from om_ai.core.agent_civilization import (
    CivilizationEngine
)


from om_ai.core.autonomous_research import (
    AutonomousResearchEngine
)
MAX_RESPONSE_RETRIES = 2


class OMCognitiveBrain:

    def __init__(self) -> None:
        self.memory = MemoryManager()
        self.intent = IntentEngine()
        self.technology = TechnologyEngine()
        self.planner = TaskPlanner()
        self.reasoning = ReasoningChain()
        self.reasoning_engine = ReasoningEngine()
        self.research_engine = ResearchEngine()
        self.freshness_detector = FreshnessDetector()
        self.leakage_detector = LeakageDetector()
        self.context_intelligence = ContextIntelligence()
        self.garbage_detector = GarbageDetector()
        self.tool_filter = ToolOutputFilter()
        self.coding_intelligence = CodingIntelligence()
        self.response_engine = ResponseEngine()
        self.quality_checker = QualityChecker()
        self.self_critic = SelfCritic()
        self.context_filter = ContextFilter()
        self.response_memory = ResponseMemory()
        self.generator = AnswerGenerator()
        self.evaluator = SelfEvaluator()
        self.agent_router = AgentRouter()
        self.agent_executor = AgentExecutor()
        self.agent_planner = AgentCollaborationPlanner()
        self.agent_coordinator = AgentCoordinator()
        self.learning_engine = LearningEngine()
        self.improvement = KnowledgeImprovementEngine()
        self.orchestrator = OMOrchestrator()
        self.reflection_engine = ReflectionEngine()
        self.memory_consolidator = MemoryConsolidator()
        self.user_intelligence = UserIntelligenceEngine()
        self.context_engine = ContextEngine()
        self.roadmap = OMRoadmapStack()
        self.knowledge_brain = KnowledgeBrain()
        self.research_pipeline = ResearchPipeline()
        self.long_context = LongContextEngine()
        self.advanced_reasoning_engine = AdvancedReasoningEngine()
        self.civilization = CivilizationEngine()
        self.autonomous_research = AutonomousResearchEngine()


    @staticmethod
    def _plan_list(state: Any) -> list[Any]:
        if state is None:
            return []
        if hasattr(state, "plan"):
            return list(getattr(state, "plan") or [])
        if isinstance(state, dict):
            return list(state.get("plan") or [])
        return []

    @staticmethod
    def _context_blob(items: Any) -> str:
        if items is None:
            return ""
        if isinstance(items, str):
            return items[:6000]
        if isinstance(items, (list, tuple)):
            parts = []
            for item in items[:10]:
                if item is None or item == "":
                    continue
                parts.append(str(item)[:2000])
            return "\n\n".join(parts)[:8000]
        return str(items)[:6000]

    def generate(
        self,
        message: str,
        *,
        knowledge: Any = None,
        memory: Any = None,
        native_chat: Callable[..., str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        message = (message or "").strip()
        stages: list[str] = []
        meta: dict[str, Any] = {"flow": "om-brain-v87"}
        research_state = None
        research = None
        caller_knowledge = knowledge
        request_context: dict[str, Any] = dict(context or {})
        long_context_pack: dict[str, Any] = {}
        advanced_reasoning: dict[str, Any] = {}

        # 0) Language detection
        stages.append("language")
        try:
            language = detect_language(message)
        except Exception:
            language = "en"
        meta["language"] = language

        # Knowledge Brain → ResearchPipeline when internal knowledge is missing
        stages.append("knowledge_brain")
        try:
            knowledge = self.knowledge_brain.analyze(message)
        except Exception as exc:
            from om_ai.core.knowledge_brain import KnowledgeContext

            knowledge = KnowledgeContext(query=message, knowledge_found=False)
            meta["knowledge_brain"] = {"error": str(exc), "knowledge_found": False}
        else:
            meta["knowledge_brain"] = {
                "knowledge_found": bool(getattr(knowledge, "knowledge_found", False)),
                "confidence": float(getattr(knowledge, "confidence", 0) or 0),
                "concepts": list(getattr(knowledge, "concepts", []) or []),
                "source": str(getattr(knowledge, "source", "internal") or "internal"),
            }

        if not getattr(knowledge, "knowledge_found", False):
            stages.append("research_pipeline")
            try:
                research = self.research_pipeline.run(message)
                meta["research_pipeline"] = (
                    research if isinstance(research, dict) else {"result": research}
                )
            except Exception as exc:
                research = None
                meta["research_pipeline"] = {"error": str(exc)}

        kb_result = knowledge
        if caller_knowledge is not None:
            knowledge = caller_knowledge
        elif getattr(kb_result, "knowledge_found", False):
            knowledge = {
                "source": "knowledge_brain",
                "concepts": list(getattr(kb_result, "concepts", []) or []),
                "confidence": float(getattr(kb_result, "confidence", 0) or 0),
                "matched_nodes": list(getattr(kb_result, "matched_nodes", []) or []),
                "knowledge_found": True,
            }
        else:
            knowledge = None

        # Early refuse meaningless / corrupted-content requests
        if self.garbage_detector.is_nonsense_request(message):
            stages.append("garbage_request_refused")
            answer = self.garbage_detector.refusal_message()
            return {
                "answer": answer,
                "status": "ok",
                "understanding": {
                    "intent": "refuse_nonsense",
                    "domain": "safety",
                    "confidence": 1.0,
                },
                "reasoning": {},
                "coding": {},
                "research": None,
                "response_state": None,
                "response_plan": {"intent": "refuse_nonsense", "response_type": "direct", "plan": []},
                "quality": {"approved": True, "score": 1.0, "issues": []},
                "stages": stages + ["answer"],
                "meta": meta,
                "intent": {"intent": "refuse_nonsense"},
                "technology": {"frameworks": []},
            }

        # 1) Understanding
        stages.append("understanding")
        understanding: dict[str, Any] = {}
        try:
            from om_ai.core.intelligence.understanding_engine import UnderstandingEngine

            understanding = UnderstandingEngine().understand(
                message,
                context=request_context,
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

        # 2) Freshness → Research
        stages.append("freshness")
        freshness = {"requires_research": False, "signals": []}
        try:
            freshness = self.freshness_detector.analyze(message)
        except Exception as exc:
            freshness = {"requires_research": False, "signals": [], "error": str(exc)}
        meta["freshness"] = freshness

        if (
            freshness.get("requires_research")
            or freshness.get("needs_research")
            or bool((research or {}).get("research_required"))
        ):
            stages.append("research")
            try:
                research_state = self.research_engine.research(
                    message,
                    understanding=understanding,
                )
                meta["research"] = {
                    "status": getattr(research_state, "status", None),
                    "sources": len(getattr(research_state, "sources", []) or []),
                    "confidence": getattr(research_state, "confidence", 0),
                    "citations": list(getattr(research_state, "citations", []) or []),
                    "from_knowledge_gap": bool((research or {}).get("research_required")),
                }
            except Exception as exc:
                research_state = None
                meta["research"] = {"error": str(exc)}

        # 2b) STEPs 83-93 roadmap enrich (long context, knowledge brain, agents, deep reasoning prep)
        stages.append("roadmap_enrich")
        roadmap_pack: dict[str, Any] = {}
        try:
            roadmap_pack = self.roadmap.enrich_before_answer(
                message,
                knowledge=knowledge,
                memory=memory,
                context=request_context,
            )
            meta["roadmap"] = {
                "status": self.roadmap.status(),
                "has_collaboration": bool(roadmap_pack.get("collaboration")),
                "has_civilization": bool(roadmap_pack.get("civilization")),
                "reasoning_mode": (roadmap_pack.get("advanced_reasoning") or {}).get("mode"),
            }
        except Exception as exc:
            roadmap_pack = {}
            meta["roadmap"] = {"error": str(exc)}

        # 3) Reasoning
        stages.append("reasoning")
        reasoning_out: dict[str, Any] = {}
        try:
            reasoning_out = self.reasoning_engine.process(message, message)
        except Exception as exc:
            reasoning_out = {"status": "error", "error": str(exc)}
        # Prefer STEP 88 deep reasoning when available
        deep = (roadmap_pack.get("advanced_reasoning") or {})
        if deep.get("plan"):
            merged_plan = list(dict.fromkeys(list(reasoning_out.get("plan") or []) + list(deep.get("plan") or [])))
            reasoning_out = {
                **reasoning_out,
                "plan": merged_plan,
                "deep": deep,
                "final_reasoning": deep.get("final_reasoning"),
            }
        meta["reasoning"] = {
            "status": reasoning_out.get("status"),
            "plan": reasoning_out.get("plan"),
            "mode": deep.get("mode"),
        }

        # 4) CodingIntelligence
        stages.append("coding_intelligence")
        coding_out: dict[str, Any] = {}
        if is_coding_task(message) or intent_name in {
            "coding",
            "debug",
            "architecture",
            "prompt_generation",
            "software_creation",
            "implementation",
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

        # 5) Response planning
        stages.append("response_engine")
        research_summary = ""
        research_citations: list[Any] = []
        if research_state is not None:
            research_summary = str(getattr(research_state, "summary_context", "") or "")
            research_citations = list(getattr(research_state, "citations", []) or [])
        try:
            response_state = self.response_engine.prepare(
                message=message,
                intent=intent_name,
                understanding=understanding,
                reasoning=reasoning_out,
                context={
                    "memory": memory,
                    "knowledge": knowledge,
                    "coding": coding_out,
                    "research": research_summary,
                    "citations": research_citations,
                },
            )
        except Exception as exc:
            from om_ai.core.response.response_state import ResponseState

            response_state = ResponseState(
                user_message=message,
                intent=intent_name,
                response_type="direct",
                plan=["Answer the user's request clearly"],
                issues=[str(exc)],
            )
        meta["response_plan"] = {
            "intent": getattr(response_state, "intent", intent_name),
            "response_type": getattr(response_state, "response_type", "direct"),
            "plan": self._plan_list(response_state),
        }

        # 6) Context Intelligence (+ research injection)
        stages.append("context_intelligence")
        raw_context: list[Any] = [knowledge, memory]
        if research_summary:
            raw_context.append(research_summary)
        if isinstance(research, dict) and research.get("task") is not None:
            raw_context.append({"research_task": research.get("task")})
        roadmap_blob = (roadmap_pack or {}).get("context_blob")
        if roadmap_blob:
            raw_context.append(roadmap_blob)
        kb_ctx = ((roadmap_pack or {}).get("knowledge_brain") or {}).get("context")
        if kb_ctx:
            raw_context.append(kb_ctx)
        try:
            filtered = self.context_filter.clean(raw_context)
        except Exception:
            filtered = [x for x in raw_context if x]
        try:
            clean_context = self.context_intelligence.process(filtered, message)
        except Exception:
            clean_context = filtered
        meta["context_intelligence"] = {"kept": len(clean_context or [])}

        # Before generating response: long-context + advanced reasoning
        stages.append("long_context")
        try:
            context = self.long_context.process(message)
            long_context_pack = context if isinstance(context, dict) else {"related_context": context}
            meta["long_context"] = {
                "context_available": bool(long_context_pack.get("context_available")),
                "related": len(list(long_context_pack.get("related_context") or [])),
            }
            related = long_context_pack.get("related_context")
            if related:
                clean_context = list(clean_context or []) + [related]
        except Exception as exc:
            long_context_pack = {}
            meta["long_context"] = {"error": str(exc)}

        stages.append("advanced_reasoning")
        try:
            reasoning = self.advanced_reasoning_engine.reason(message)
            advanced_reasoning = reasoning if isinstance(reasoning, dict) else {"result": reasoning}
            meta["advanced_reasoning"] = {
                "analysis": advanced_reasoning.get("analysis"),
                "plan": advanced_reasoning.get("plan"),
            }
            adv_plan = advanced_reasoning.get("plan")
            if isinstance(adv_plan, list) and adv_plan:
                merged_plan = list(
                    dict.fromkeys(list(reasoning_out.get("plan") or []) + [str(x) for x in adv_plan])
                )
                reasoning_out = {
                    **reasoning_out,
                    "plan": merged_plan,
                    "advanced": advanced_reasoning,
                }
            elif advanced_reasoning:
                reasoning_out = {**reasoning_out, "advanced": advanced_reasoning}
            meta["reasoning"] = {
                "status": reasoning_out.get("status"),
                "plan": reasoning_out.get("plan"),
                "mode": (roadmap_pack.get("advanced_reasoning") or {}).get("mode"),
                "advanced": True,
            }
        except Exception as exc:
            advanced_reasoning = {}
            meta["advanced_reasoning"] = {"error": str(exc)}

        # 7) OM Native Model
        stages.append("om_native_model")
        draft = self._native_or_fallback_answer(
            message,
            understanding=understanding,
            reasoning=reasoning_out,
            coding=coding_out,
            prepared=response_state,
            knowledge=clean_context,
            memory=clean_context,
            research=research_summary,
            native_chat=native_chat,
        )
        if not (draft or "").strip() and intent_name in {
            "conversation",
            "greeting",
            "casual_conversation",
        }:
            draft = self._safe_fallback(message, intent_name)
        meta["model"] = {"chars": len(draft or "")}

        # 8) Leakage → Garbage → SelfCritic → Quality → regenerate
        stages.append("leakage_detector")
        regenerate = False
        if self.leakage_detector.check(draft or ""):
            regenerate = True
            draft = ""
            meta["leakage"] = True
        else:
            meta["leakage"] = False

        stages.append("garbage_detector")
        if self.garbage_detector.check(draft or ""):
            regenerate = True
            meta["garbage"] = True
        else:
            meta["garbage"] = False

        stages.append("tool_filter")
        cleaned_tools = self.tool_filter.clean(draft or "")
        if (draft or "") and not cleaned_tools:
            regenerate = True
            draft = ""
            meta["tool_leakage"] = True
        else:
            if cleaned_tools != (draft or "").strip():
                draft = cleaned_tools
                meta["tool_leakage_cleaned"] = True
            else:
                meta["tool_leakage"] = False

        stages.append("quality_checker")
        quality = self.quality_checker.validate(
            response=draft,
            original_message=message,
        )
        critic = self.self_critic.review(message, draft or "")
        meta["self_critic"] = critic
        if not critic.get("approved"):
            quality = {
                **quality,
                "approved": False,
                "issues": list(
                    dict.fromkeys(
                        list(quality.get("issues") or [])
                        + list(critic.get("issues") or [])
                    )
                ),
            }

        try:
            response_state = self.response_engine.validate(
                state=response_state,
                response=draft or "",
            )
            if not response_state.approved:
                quality = {
                    "approved": False,
                    "score": float(response_state.quality_score or 0),
                    "issues": list(response_state.issues or quality.get("issues") or []),
                }
        except Exception:
            pass

        if regenerate:
            quality = {**quality, "approved": False}

        retry_count = 0
        while (not quality.get("approved")) and retry_count < MAX_RESPONSE_RETRIES:
            retry_count += 1
            stages.append(f"regenerate_{retry_count}")
            try:
                retry_prompt = self.response_engine.retry_instruction(response_state)
            except Exception:
                retry_prompt = (
                    f"Improve this answer for the user request.\n"
                    f"Request: {message}\n"
                    f"Issues: {', '.join(quality.get('issues') or [])}"
                )

            draft = self._native_or_fallback_answer(
                retry_prompt,
                understanding=understanding,
                reasoning=reasoning_out,
                coding=coding_out,
                prepared=response_state,
                knowledge=clean_context,
                memory=clean_context,
                research=research_summary,
                native_chat=native_chat,
            )
            generated_text = str(draft or "")

            regenerate = bool(self.garbage_detector.check(generated_text))
            if self.leakage_detector.check(generated_text):
                regenerate = True
                draft = ""
            else:
                cleaned_tools = self.tool_filter.clean(generated_text)
                if generated_text and not cleaned_tools:
                    regenerate = True
                    draft = ""
                else:
                    draft = cleaned_tools

            quality = self.quality_checker.validate(
                response=draft,
                original_message=message,
            )
            critic = self.self_critic.review(message, draft or "")
            meta["self_critic"] = critic
            if not critic.get("approved"):
                quality = {
                    **quality,
                    "approved": False,
                    "issues": list(
                        dict.fromkeys(
                            list(quality.get("issues") or [])
                            + list(critic.get("issues") or [])
                        )
                    ),
                }
            if regenerate:
                quality = {**quality, "approved": False}

            try:
                response_state = self.response_engine.validate(
                    state=response_state,
                    response=draft or "",
                )
            except Exception:
                pass

        meta["quality"] = quality
        meta["retries"] = retry_count

        if not quality.get("approved"):
            if intent_name in {"conversation", "greeting", "casual_conversation"}:
                answer = self._safe_fallback(message, intent_name)
                self._store_long_context_turn(message, answer, meta)
                return {
                    "answer": answer,
                    "status": "ok_fallback",
                    "quality": quality,
                    "understanding": understanding,
                    "reasoning": reasoning_out,
                    "coding": coding_out,
                    "research": meta.get("research"),
                    "long_context": long_context_pack or meta.get("long_context"),
                    "advanced_reasoning": advanced_reasoning or meta.get("advanced_reasoning"),
                    "response_state": response_state,
                    "response_plan": meta.get("response_plan"),
                    "stages": stages + ["answer", "long_context_store"],
                    "meta": meta,
                    "intent": understanding,
                    "technology": {
                        "frameworks": meta["coding"].get("frameworks") or [],
                    },
                }
            if research_summary or research_citations:
                try:
                    research_answer = self.response_engine.format_research_answer(
                        message=message,
                        draft="",
                        research_summary=research_summary,
                        citations=research_citations,
                        freshness_signals=list(freshness.get("signals") or []),
                    )
                except Exception:
                    research_answer = ""
                if research_answer:
                    self._store_long_context_turn(message, research_answer, meta)
                    return {
                        "answer": research_answer,
                        "status": "ok_research_fallback",
                        "quality": quality,
                        "understanding": understanding,
                        "reasoning": reasoning_out,
                        "coding": coding_out,
                        "research": meta.get("research"),
                        "long_context": long_context_pack or meta.get("long_context"),
                        "advanced_reasoning": advanced_reasoning or meta.get("advanced_reasoning"),
                        "response_state": response_state,
                        "response_plan": meta.get("response_plan"),
                        "stages": stages + ["answer", "long_context_store"],
                        "meta": meta,
                        "intent": understanding,
                        "technology": {
                            "frameworks": meta["coding"].get("frameworks") or [],
                        },
                    }
            fail_answer = "OM could not generate a reliable response."
            self._store_long_context_turn(message, fail_answer, meta)
            return {
                "answer": fail_answer,
                "status": "generation_failed",
                "quality": quality,
                "understanding": understanding,
                "reasoning": reasoning_out,
                "coding": coding_out,
                "research": meta.get("research"),
                "long_context": long_context_pack or meta.get("long_context"),
                "advanced_reasoning": advanced_reasoning or meta.get("advanced_reasoning"),
                "response_state": response_state,
                "response_plan": meta.get("response_plan"),
                "stages": stages + ["long_context_store"],
                "meta": meta,
                "intent": understanding,
                "technology": {
                    "frameworks": meta["coding"].get("frameworks") or [],
                },
            }

        stages.append("answer")
        answer = (draft or "").strip()
        if not answer:
            answer = self._safe_fallback(message, intent_name)

        # Architecture / build tasks: attach collaboration board when useful
        collab = (roadmap_pack or {}).get("collaboration") or {}
        if collab.get("summary") and (
            intent_name in {"architecture", "coding", "software_creation", "implementation"}
            or any(w in message.lower() for w in ("design", "architect", "build", "ecommerce", "uber"))
        ):
            if len((answer or "").split()) < 80:
                answer = (answer + "\n\n" + collab["summary"]).strip() if answer else collab["summary"]
            meta["collaboration_attached"] = True

        # Format research answers with human-facing Sources block
        # whenever freshness triggered research (even if sources are thin).
        if freshness.get("requires_research") or research_summary or research_citations:
            try:
                formatted = self.response_engine.format_research_answer(
                    message=message,
                    draft=answer,
                    research_summary=research_summary,
                    citations=research_citations,
                    freshness_signals=list(freshness.get("signals") or []),
                )
                if formatted:
                    answer = formatted
            except Exception:
                pass

        # Tool-trace scrub on final answer
        tool_cleaned = self.tool_filter.clean(answer)
        if answer and not tool_cleaned:
            answer = "OM could not verify a reliable answer."
            meta["tool_leakage_final"] = True
        else:
            answer = tool_cleaned or answer

        if self.leakage_detector.check(answer):
            # Allow "Sources:" in research answers — leakage blocks "Source:" training leak.
            # Re-check after stripping a leading Sources section if present.
            probe = answer
            if "Sources:" in probe:
                probe = probe.split("Sources:")[0]
            if self.leakage_detector.check(probe):
                answer = "OM could not verify a reliable answer."
                meta["leakage_final"] = True

        try:
            self.response_memory.remember(
                intent_name,
                {"answer": answer[:500], "score": quality.get("score")},
            )
        except Exception:
            pass

        # STEPs 83/84/91/93 continuous + advanced learning + self-improve + training queue
        stages.append("roadmap_learn")
        try:
            meta["roadmap_learn"] = self.roadmap.learn_after_answer(
                message,
                answer,
                quality=quality,
                meta={"intent": intent_name, "research": meta.get("research")},
            )
        except Exception as exc:
            meta["roadmap_learn"] = {"error": str(exc)}

        # After response: persist turn into long-context memory
        stages.append("long_context_store")
        self._store_long_context_turn(message, answer, meta)

        return {
            "answer": answer,
            "status": "ok",
            "understanding": understanding,
            "reasoning": reasoning_out,
            "coding": coding_out,
            "research": meta.get("research"),
            "long_context": long_context_pack or meta.get("long_context"),
            "advanced_reasoning": advanced_reasoning or meta.get("advanced_reasoning"),
            "response_state": response_state,
            "response_plan": meta.get("response_plan"),
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
        prepared: Any,
        knowledge: Any,
        memory: Any,
        research: Any = None,
        native_chat: Callable[..., str] | None = None,
    ) -> str:
        intent_name = str(understanding.get("intent") or "")
        if intent_name == "conversation":
            pass

        knowledge_text = self._context_blob(knowledge)
        memory_text = self._context_blob(memory)
        research_text = self._context_blob(research)

        plan = reasoning.get("plan") or self._plan_list(prepared)
        coding_note = ""
        if coding:
            req = coding.get("requirement") or {}
            if req:
                coding_note = f"Coding context: {req}"

        response_instruction = ""
        try:
            response_instruction = self.response_engine.generation_instruction(prepared)
        except Exception:
            response_instruction = ""

        system_content = f"""
You are OM AI.

Reason carefully.
Use provided context when relevant.
Do not reveal internal tools.
Do not output training examples or dataset rows.
Do not dump unrelated README / file contents.

Intent: {intent_name}
Plan: {'; '.join(str(p) for p in (plan or [])[:6])}
{coding_note}

Context:
{knowledge_text}

Memory:
{memory_text}

Research:
{research_text}
""".strip()
        if response_instruction:
            system_content = system_content + "\n\n" + response_instruction

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": message},
        ]

        if callable(native_chat):
            try:
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
                text = str(backend.chat(messages) or "").strip()
                if text:
                    return text
        except Exception:
            pass

        if research_text.strip():
            return (
                "Based on retrieved research context:\n\n"
                + research_text[:1500]
                + "\n\n(Verify details from the cited sources when possible.)"
            )

        try:
            if coding and isinstance(coding, dict) and not coding.get("error"):
                req = coding.get("requirement") or {}
                arch = coding.get("architecture") or {}
                lines = ["Here is a clear plan for your coding request.", ""]
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
                    "plan": plan,
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

    def _store_long_context_turn(self, message: str, answer: str, meta: dict[str, Any]) -> None:
        try:
            self.long_context.store("user", message)
            self.long_context.store("assistant", answer)
            meta["long_context_store"] = {"stored": True}
        except Exception as exc:
            meta["long_context_store"] = {"error": str(exc)}

    def _safe_fallback(self, message: str, intent_name: str) -> str:
        if intent_name == "conversation" or is_greeting(message):
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
        memory_context = {"relevant": relevant_memory, "knowledge": knowledge}
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
            qcheck = self.quality_checker.validate(
                response=intel_answer,
                original_message=question,
            )
            if qcheck.get("approved") and not self.leakage_detector.check(intel_answer):
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
                "self_critic": (generated_flow.get("meta") or {}).get("self_critic"),
                "research": generated_flow.get("research"),
                "approved": bool(
                    evaluation.get("approved", True) and flow_quality.get("approved", True)
                ),
            }

        improvement_result = self.improvement.improve(
            question,
            user_answer,
            evaluation,
        )
        learning_result = self.learning_engine.learn(
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
                "research": generated_flow.get("research"),
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
