"""
OM Production Brain
===================

Single production orchestration layer for OM AI.

Architecture:

    User
      |
      v
    Router
      |
      v
    Context / Intelligence
      |
      v
    OMBrainController
      |
      +---- Reasoning
      +---- Knowledge
      +---- Memory
      +---- Solution planning
      +---- Tool/action intelligence
      |
      v
    Native OM Model
      |
      v
    Verification / Safety
      |
      v
    Response Quality
      |
      v
    Final Answer

Important:

- The native OM model is the primary generation source.
- This class does not recursively call chatgpt_runtime.
- Specialized engines are used for intelligence/routing.
- Static/template answers are rejected when possible.
- All failures are handled without crashing the chat server.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from om_ai.core.chatgpt_runtime import OMBrainController

from om_ai.core.chat_intelligence import (
    ConversationRouter,
    CodingEngine,
    ResearchEngine,
    EmotionalEngine,
    ActionEngine,
    SolutionPlanner,
    UserPreference,
    VerificationEngine,
    AnswerPlanner,
    ChatOrchestrator,
    ChatQualityEngine,
    ProblemAnalyzer,
    ReasoningEngine,
    ResponseOptimizer,
    SafetyFilter,
    SolutionEngine,
    SolutionMemory,
)

from om_ai.core.observability import (
    ActivityEvent,
    ActivityType,
    ObservabilityEngine,
)


logger = logging.getLogger("OMProductionBrain")


class OMProductionBrain:
    """
    Production entry point for the OM intelligence system.

    The purpose of this class is NOT to be another LLM.

    It is the orchestration layer that connects:

        conversation
        context
        routing
        reasoning
        memory
        knowledge
        solutions
        native model generation
        verification
        safety
        response quality

    into one coherent execution path.

    Canonical flow:

        USER
          |
          v
        ROUTER
          |
          v
        INTELLIGENCE
          |
          v
        CONTROLLER
          |
          v
        NATIVE MODEL
          |
          v
        VERIFICATION
          |
          v
        SAFETY
          |
          v
        QUALITY
          |
          v
        FINAL ANSWER
    """

    def __init__(self) -> None:
        # ---------------------------------------------------------
        # Observability
        # ---------------------------------------------------------

        self.observability = ObservabilityEngine()

        # ---------------------------------------------------------
        # Main brain controller
        # ---------------------------------------------------------

        self.controller = OMBrainController()

        # ---------------------------------------------------------
        # Conversation routing
        # ---------------------------------------------------------

        self.conversation_router = ConversationRouter()

        # ---------------------------------------------------------
        # Intelligence engines
        # ---------------------------------------------------------

        self.coding_engine = CodingEngine()
        self.research_engine = ResearchEngine()
        self.emotional_engine = EmotionalEngine()
        self.action_engine = ActionEngine()

        # ---------------------------------------------------------
        # Planning
        # ---------------------------------------------------------

        self.solution_planner = SolutionPlanner()
        self.answer_planner = AnswerPlanner()

        # ---------------------------------------------------------
        # User / personal context
        # ---------------------------------------------------------

        self.user_preference = UserPreference()
        self.solution_memory = SolutionMemory()

        # ---------------------------------------------------------
        # Problem / reasoning
        # ---------------------------------------------------------

        self.problem_analyzer = ProblemAnalyzer()
        self.reasoning_engine = ReasoningEngine()

        # ---------------------------------------------------------
        # Verification / response
        # ---------------------------------------------------------

        self.verification_engine = VerificationEngine()
        self.response_optimizer = ResponseOptimizer()
        self.chat_quality_engine = ChatQualityEngine()
        self.safety_filter = SafetyFilter()

        # ---------------------------------------------------------
        # Solution engine
        #
        # Some versions of OM use a dependency-injected SolutionEngine.
        # Keep this compatible with both implementations.
        # ---------------------------------------------------------

        self.solution_engine = self._build_solution_engine()

        # ---------------------------------------------------------
        # Chat orchestration
        # ---------------------------------------------------------

        self.chat_orchestrator = ChatOrchestrator()

    # ==================================================================
    # COMPONENT INITIALIZATION
    # ==================================================================

    def _build_solution_engine(self) -> Any:
        """
        Build SolutionEngine while remaining compatible with both:

            SolutionEngine()

        and:

            SolutionEngine(
                problem_analyzer=...,
                reasoning_engine=...,
                solution_planner=...,
                verification_engine=...,
            )

        This prevents a constructor mismatch from breaking startup.
        """

        try:
            return SolutionEngine(
                problem_analyzer=self.problem_analyzer,
                reasoning_engine=self.reasoning_engine,
                solution_planner=self.solution_planner,
                verification_engine=self.verification_engine,
            )
        except TypeError:
            return SolutionEngine()

    # ==================================================================
    # NATIVE MODEL BRIDGE
    # ==================================================================

    def _model_generate(
        self,
        prompt: str,
        context: str = "",
    ) -> str:
        """
        Generate using the actual OM native model.

        IMPORTANT:

        This method deliberately does NOT call:

            run_chatgpt_runtime()
            OMBrainController.run()

        Otherwise the architecture could recursively enter itself.

        Preferred path:

            api.main.native_backend.chat()

        Secondary path:

            api.main.engine.chat()

        Last-resort path:

            build_real_answer()

        The last-resort path is not considered the primary intelligence
        source; it only prevents an empty response when the native model
        is unavailable.
        """

        prompt = str(prompt or "").strip()

        if not prompt:
            return ""

        try:
            native = None
            engine = None

            # ---------------------------------------------------------
            # Obtain the already-loaded native runtime.
            # ---------------------------------------------------------

            try:
                from om_ai.api import main as api_main

                native = getattr(api_main, "native_backend", None)
                engine = getattr(api_main, "engine", None)

            except Exception as exc:
                logger.debug(
                    "Unable to access native API runtime: %s",
                    exc,
                )

            # ---------------------------------------------------------
            # Build model messages.
            # ---------------------------------------------------------

            messages: list[dict[str, str]] = []

            if context:
                messages.append(
                    {
                        "role": "system",
                        "content": str(context)[:8000],
                    }
                )

            messages.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )

            # ---------------------------------------------------------
            # Primary native model path.
            # ---------------------------------------------------------

            native_ready = bool(
                native is not None
                and getattr(native, "loaded", False)
                and getattr(native, "_trained", False)
                and callable(getattr(native, "chat", None))
            )

            if native_ready:
                chat_fn = getattr(native, "chat", None)

                if callable(chat_fn):
                    try:
                        result = chat_fn(messages)

                        text = str(result or "").strip()

                        if text:
                            return text

                    except Exception as exc:
                        logger.debug(
                            "Native structured chat failed: %s",
                            exc,
                        )

                    # Some OM native implementations accept a plain string.
                    try:
                        result = chat_fn(prompt)

                        text = str(result or "").strip()

                        if text:
                            return text

                    except Exception as exc:
                        logger.debug(
                            "Native plain chat failed: %s",
                            exc,
                        )

            # ---------------------------------------------------------
            # Secondary engine path.
            # ---------------------------------------------------------

            if engine is not None:
                model = getattr(engine, "model", None)

                chat_fn = getattr(engine, "chat", None)

                if model is not None and callable(chat_fn):
                    try:
                        result = chat_fn(messages)

                        text = str(result or "").strip()

                        if text:
                            return text

                    except Exception as exc:
                        logger.debug(
                            "Engine structured chat failed: %s",
                            exc,
                        )

                    try:
                        result = chat_fn(prompt)

                        text = str(result or "").strip()

                        if text:
                            return text

                    except Exception as exc:
                        logger.debug(
                            "Engine plain chat failed: %s",
                            exc,
                        )

            # ---------------------------------------------------------
            # Last-resort dynamic answer builder.
            # ---------------------------------------------------------

            try:
                from om_ai.core.intelligence.real_answer import (
                    build_real_answer,
                )

                result = build_real_answer(prompt)

                text = str(result or "").strip()

                if text:
                    return text

            except Exception as exc:
                logger.debug(
                    "Real-answer fallback failed: %s",
                    exc,
                )

        except Exception:
            logger.exception(
                "OM native model generation failed"
            )

        return ""

    # ==================================================================
    # RESPONSE CLEANING
    # ==================================================================

    @staticmethod
    def _clean_answer(answer: Any) -> str:
        """
        Clean an answer before it is allowed to become the final response.

        Rejects:
        - empty responses
        - known solution stubs
        - known static/template responses
        """

        text = str(answer or "").strip()

        if not text:
            return ""

        # -------------------------------------------------------------
        # Reject known solution stubs.
        # -------------------------------------------------------------

        try:
            from om_ai.core.chat_intelligence.stub_detect import (
                is_solution_stub,
            )

            if is_solution_stub(text):
                return ""

        except Exception:
            pass

        # -------------------------------------------------------------
        # Reject known static/template responses.
        # -------------------------------------------------------------

        try:
            from om_ai.core.intelligence.real_answer import (
                looks_like_static_reply,
            )

            if looks_like_static_reply(text):
                return ""

        except Exception:
            pass

        return text

    # ==================================================================
    # SAFE FALLBACK
    # ==================================================================

    @staticmethod
    def _fallback_answer(
        message: str,
        route_type: str = "",
    ) -> str:
        """
        Minimal emergency fallback.

        This should almost never be reached.

        It intentionally avoids the old repetitive chatbot responses.
        """

        message = str(message or "").strip()

        if not message:
            return "I'm listening."

        if route_type == "emotional":
            return (
                "I'm here with you. "
                "Tell me what is going on."
            )

        if route_type == "action":
            return (
                "I understand the request. "
                "I need a little more information before I take an action."
            )

        if route_type == "research":
            return (
                "I understand what you want to find. "
                "Let me work through the information first."
            )

        return (
            "I understand the request. "
            "Let me work through it carefully."
        )

    # ==================================================================
    # ROUTE
    # ==================================================================

    def _route(
        self,
        message: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Route the request through the existing conversation router.
        """

        try:
            route = self.conversation_router.route(
                message,
                context=context,
            )

            if isinstance(route, dict):
                return route

        except Exception:
            logger.exception(
                "Conversation routing failed"
            )

        return {
            "route": "conversation",
            "reason": "router_fallback",
            "confidence": 0.0,
        }

    # ==================================================================
    # SPECIALIZED INTELLIGENCE
    # ==================================================================

    def _specialized_answer(
        self,
        message: str,
        route_type: str,
        context: dict[str, Any],
    ) -> str:
        """
        Give specialized engines an opportunity to handle requests.

        IMPORTANT:

        The native LLM remains the primary path for normal conversation.

        Specialized engines are used when the route explicitly indicates
        a specialized capability.
        """

        try:

            # ---------------------------------------------------------
            # Emotional conversation
            # ---------------------------------------------------------

            if route_type == "emotional":
                return self._clean_answer(
                    self.emotional_engine.respond(
                        message,
                        context=context,
                    )
                )

            # ---------------------------------------------------------
            # Research
            # ---------------------------------------------------------

            if route_type == "research":
                return self._clean_answer(
                    self.research_engine.research(
                        message
                    )
                )

            # ---------------------------------------------------------
            # Action
            # ---------------------------------------------------------

            if route_type == "action":
                return self._clean_answer(
                    self.action_engine.execute(
                        message,
                        context=context,
                    )
                )

        except Exception:
            logger.exception(
                "Specialized intelligence failed"
            )

        return ""

    # ==================================================================
    # MAIN PROCESS
    # ==================================================================

    def process(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Main production entry point.

        This is the method the application should call for an OM response.

        Returns a stable response envelope:

            {
                "success": True,
                "answer": "...",
                "route": {...},
                "trace_id": "...",
                "meta": {...}
            }
        """

        message = str(message or "").strip()
        context = dict(context or {})

        # -------------------------------------------------------------
        # Empty input
        # -------------------------------------------------------------

        if not message:
            return {
                "success": False,
                "answer": "",
                "route": {
                    "route": "conversation",
                    "reason": "empty_message",
                },
                "trace_id": None,
                "error": "empty_message",
            }

        # -------------------------------------------------------------
        # Trace
        # -------------------------------------------------------------

        trace = self.observability.start_trace()

        try:

            # =========================================================
            # EVENT: REQUEST
            # =========================================================

            self.observability.log(
                trace,
                ActivityEvent(
                    type=ActivityType.THINKING,
                    title="Processing user request",
                    description=(
                        "OM production intelligence pipeline"
                    ),
                    metadata={
                        "message_length": len(message),
                    },
                ),
            )

            # =========================================================
            # 1. ROUTE
            # =========================================================

            route = self._route(
                message,
                context,
            )

            route_type = str(
                route.get("route")
                or "conversation"
            )

            self.observability.log(
                trace,
                ActivityEvent(
                    type=ActivityType.THINKING,
                    title="Conversation routing",
                    description=str(
                        route.get("reason")
                        or "Request routed"
                    ),
                    metadata=route,
                ),
            )

            # =========================================================
            # 2. BUILD MODEL CONTEXT
            # =========================================================

            model_context_parts: list[str] = []

            # User-provided runtime context.
            if context:
                model_context_parts.append(
                    "RUNTIME CONTEXT:\n"
                    + str(context)[:8000]
                )

            # Route information.
            model_context_parts.append(
                "REQUEST ROUTE:\n"
                + str(route)
            )

            # ---------------------------------------------------------
            # Optional preference context.
            # ---------------------------------------------------------

            try:
                preferences = self.user_preference

                if preferences is not None:
                    model_context_parts.append(
                        "USER PREFERENCE CONTEXT:\n"
                        + str(preferences)[:3000]
                    )

            except Exception:
                pass

            model_context = "\n\n".join(
                model_context_parts
            )

            # =========================================================
            # 3. SPECIALIZED INTELLIGENCE
            # =========================================================

            answer = self._specialized_answer(
                message,
                route_type,
                context,
            )

            # =========================================================
            # 4. PRIMARY LLM / OM BRAIN
            # =========================================================

            if not answer:

                try:

                    pack = self.controller.run(
                        message,
                        model_generate=self._model_generate,
                        extra={
                            **context,
                            "route": route,
                            "model_context": model_context,
                        },
                    )

                    if isinstance(pack, dict):

                        answer = self._clean_answer(
                            pack.get("answer")
                        )

                    else:
                        answer = self._clean_answer(
                            pack
                        )

                except Exception:
                    logger.exception(
                        "OMBrainController failed"
                    )

                    answer = ""

            # =========================================================
            # 5. SOLUTION ENGINE FALLBACK
            # =========================================================

            if not answer and route_type in {
                "problem_solving",
                "coding",
                "technical",
            }:

                try:

                    result = self.solution_engine.solve(
                        message,
                        context=context,
                        model_generate=self._model_generate,
                    )

                    if isinstance(result, dict):

                        answer = self._clean_answer(
                            result.get("answer")
                        )

                except TypeError:

                    # Compatibility with older SolutionEngine
                    # implementations that don't accept model_generate.

                    try:

                        result = self.solution_engine.solve(
                            message,
                            context=context,
                        )

                        if isinstance(result, dict):
                            answer = self._clean_answer(
                                result.get("answer")
                            )

                    except Exception:
                        logger.exception(
                            "SolutionEngine compatibility path failed"
                        )

                except Exception:
                    logger.exception(
                        "SolutionEngine failed"
                    )

            # =========================================================
            # 6. FINAL DYNAMIC ANSWER FALLBACK
            # =========================================================

            if not answer:

                try:

                    from om_ai.core.intelligence.real_answer import (
                        build_real_answer,
                    )

                    answer = self._clean_answer(
                        build_real_answer(
                            message
                        )
                    )

                except Exception:
                    logger.debug(
                        "Dynamic answer fallback unavailable"
                    )

            # =========================================================
            # 7. EMERGENCY FALLBACK
            # =========================================================

            if not answer:

                answer = self._fallback_answer(
                    message,
                    route_type,
                )

            # =========================================================
            # 8. SAFETY
            # =========================================================

            try:

                safe = self.safety_filter.filter(
                    answer
                )

                if isinstance(safe, dict):

                    safe_answer = safe.get(
                        "answer"
                    )

                    if safe_answer:
                        answer = str(
                            safe_answer
                        ).strip()

                elif safe:
                    answer = str(
                        safe
                    ).strip()

            except Exception:
                logger.exception(
                    "Safety filter failed"
                )

            # =========================================================
            # 9. QUALITY IMPROVEMENT
            # =========================================================

            try:

                improved = self.chat_quality_engine.improve(
                    answer or "",
                    question=message,
                )

                improved = self._clean_answer(
                    improved
                )

                if improved:
                    answer = improved

            except Exception:
                logger.exception(
                    "Chat quality improvement failed"
                )

            # =========================================================
            # 10. RESPONSE OPTIMIZATION
            # =========================================================

            try:

                optimizer = self.response_optimizer

                if optimizer is not None:

                    optimize_fn = getattr(
                        optimizer,
                        "optimize",
                        None,
                    )

                    if callable(optimize_fn):

                        optimized = optimize_fn(
                            answer,
                            question=message,
                            context=context,
                        )

                        optimized = self._clean_answer(
                            optimized
                        )

                        if optimized:
                            answer = optimized

            except TypeError:
                # Compatibility with older optimizer signatures.
                pass

            except Exception:
                logger.exception(
                    "Response optimizer failed"
                )

            # =========================================================
            # 11. FINAL EVENT
            # =========================================================

            self.observability.log(
                trace,
                ActivityEvent(
                    type=ActivityType.RESPONSE,
                    title="OM response generated",
                    description=(
                        "Production intelligence pipeline completed"
                    ),
                    metadata={
                        "route": route_type,
                        "answer_length": len(
                            answer or ""
                        ),
                    },
                ),
            )

            # =========================================================
            # 12. FINAL RESPONSE
            # =========================================================

            return {
                "trace_id": getattr(
                    trace,
                    "trace_id",
                    None,
                ),
                "answer": answer,
                "route": route,
                "success": True,
                "meta": {
                    "route_type": route_type,
                    "answer_length": len(
                        answer or ""
                    ),
                    "model_generation": True,
                    "production_brain": True,
                },
            }

        # =============================================================
        # GLOBAL FAILURE PROTECTION
        # =============================================================

        except Exception as exc:

            logger.exception(
                "OM Production Brain failure"
            )

            return {
                "trace_id": getattr(
                    trace,
                    "trace_id",
                    None,
                ),
                "success": False,
                "answer": self._fallback_answer(
                    message,
                    "",
                ),
                "route": {
                    "route": "error",
                },
                "error": str(exc),
                "meta": {
                    "production_brain": True,
                    "failed": True,
                },
            }


# ======================================================================
# SINGLETON / APPLICATION HELPER
# ======================================================================

_PRODUCTION_BRAIN: OMProductionBrain | None = None


def get_production_brain() -> OMProductionBrain:
    """
    Return the shared production brain instance.

    Keeping one instance prevents unnecessary recreation of all
    intelligence engines for every request.
    """

    global _PRODUCTION_BRAIN

    if _PRODUCTION_BRAIN is None:
        _PRODUCTION_BRAIN = OMProductionBrain()

    return _PRODUCTION_BRAIN


def reset_production_brain() -> None:
    """
    Reset the singleton.

    Useful for:
    - tests
    - development
    - configuration reloads
    """

    global _PRODUCTION_BRAIN

    _PRODUCTION_BRAIN = None


def run_production_brain(
    message: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Convenience function for application/API callers.
    """

    return get_production_brain().process(
        message,
        context=context,
    )


__all__ = [
    "OMProductionBrain",
    "get_production_brain",
    "reset_production_brain",
    "run_production_brain",
]