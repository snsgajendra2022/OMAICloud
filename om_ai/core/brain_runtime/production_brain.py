from __future__ import annotations

import logging

from om_ai.core.chatgpt_runtime import OMBrainController, run_chatgpt_runtime
from om_ai.core.observability import (
    ActivityEvent,
    ActivityType,
    ObservabilityEngine,
)
from om_ai.core.chat_intelligence import ConversationRouter
from om_ai.core.chat_intelligence import CodingEngine
from om_ai.core.chat_intelligence import ResearchEngine
from om_ai.core.chat_intelligence import EmotionalEngine
from om_ai.core.chat_intelligence import ActionEngine
from om_ai.core.chat_intelligence import SolutionPlanner
from om_ai.core.chat_intelligence import UserPreference
from om_ai.core.chat_intelligence import VerificationEngine
from om_ai.core.chat_intelligence import AnswerPlanner
from om_ai.core.chat_intelligence import ChatOrchestrator
from om_ai.core.chat_intelligence import ChatQualityEngine
from om_ai.core.chat_intelligence import ProblemAnalyzer
from om_ai.core.chat_intelligence import ReasoningEngine
from om_ai.core.chat_intelligence import ResponseOptimizer
from om_ai.core.chat_intelligence import SafetyFilter
from om_ai.core.chat_intelligence import SolutionEngine
from om_ai.core.chat_intelligence import SolutionMemory


logger = logging.getLogger("OMProductionBrain")


class OMProductionBrain:
    """
    Production brain front door — STEP 30 ChatGPT-like controller.

    User → Chat Intelligence → Brain Router → Response Intelligence → Answer
    """

    def __init__(self) -> None:
        self.observability = ObservabilityEngine()
        self.controller = OMBrainController()
        self.conversation_router = ConversationRouter()
        self.coding_engine = CodingEngine()
        self.research_engine = ResearchEngine()
        self.emotional_engine = EmotionalEngine()
        self.action_engine = ActionEngine()
        self.solution_planner = SolutionPlanner()
        self.user_preference = UserPreference()
        self.verification_engine = VerificationEngine()
        self.answer_planner = AnswerPlanner()
        self.chat_orchestrator = ChatOrchestrator()
        self.chat_quality_engine = ChatQualityEngine()
        self.problem_analyzer = ProblemAnalyzer()
        self.reasoning_engine = ReasoningEngine()
        self.response_optimizer = ResponseOptimizer()
        self.safety_filter = SafetyFilter()
        self.solution_engine = SolutionEngine()
        self.solution_memory = SolutionMemory()
    
    def process(self, message: str):
        trace = self.observability.start_trace()
        self.observability.log(
            trace,
            ActivityEvent(
                type=ActivityType.THINKING,
                title="Processing user request",
                description="STEP 30 OM Brain Controller",
                metadata={"message_length": len(message or "")},
            ),
        )

        pack = (
            self.controller.run(message)
            if self.controller
            else run_chatgpt_runtime(message)
        )

        self.observability.log(
            trace,
            ActivityEvent(
                type=ActivityType.RESPONSE,
                title="ChatGPT-like runtime completed",
                description="Understand → Solve → Improve → Answer",
                metadata={
                    "source": pack.get("source"),
                    "stages": list(pack.get("stages") or [])[:12],
                },
            ),
        )

        return {
            "trace_id": getattr(trace, "trace_id", None),
            "response": pack,
            "answer": pack.get("answer") or "",
            "context_blob": pack.get("context_blob") or "",
            "meta": pack.get("meta") or {},
            "stages": pack.get("stages") or [],
            "chat_intelligence": pack.get("chat_intelligence") or {},
        }
from __future__ import annotations

import logging
from typing import Any


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


from om_ai.core.chatgpt_runtime import (
    OMBrainController,
    run_chatgpt_runtime,
)


from om_ai.core.observability import (
    ActivityEvent,
    ActivityType,
    ObservabilityEngine,
)


logger = logging.getLogger(
    "OMProductionBrain"
)



class OMProductionBrain:
    """
    OM AI Production Intelligence Controller


    Complete pipeline:

    User
      |
      |
    Router
      |
      |
    Intelligence Engines
      |
      |
    Reasoning
      |
      |
    Solution
      |
      |
    Verification
      |
      |
    Response Intelligence
      |
      |
    Final Answer
    """


    def __init__(self):


        # Observability

        self.observability = (
            ObservabilityEngine()
        )


        # Base brain

        self.controller = (
            OMBrainController()
        )


        # Routing

        self.conversation_router = (
            ConversationRouter()
        )


        # Intelligence engines

        self.coding_engine = (
            CodingEngine()
        )

        self.research_engine = (
            ResearchEngine()
        )

        self.emotional_engine = (
            EmotionalEngine()
        )

        self.action_engine = (
            ActionEngine()
        )


        # Reasoning stack

        self.problem_analyzer = (
            ProblemAnalyzer()
        )

        self.reasoning_engine = (
            ReasoningEngine()
        )

        self.solution_engine = (
            SolutionEngine(
                problem_analyzer=
                    self.problem_analyzer,

                reasoning_engine=
                    self.reasoning_engine,

                solution_planner=
                    SolutionPlanner(),

                verification_engine=
                    VerificationEngine(),
            )
        )


        # Memory

        self.solution_memory = (
            SolutionMemory()
        )


        self.user_preference = (
            UserPreference()
        )


        # Response layer

        self.answer_planner = (
            AnswerPlanner()
        )


        self.response_optimizer = (
            ResponseOptimizer()
        )


        self.chat_quality_engine = (
            ChatQualityEngine()
        )


        self.safety_filter = (
            SafetyFilter()
        )


        self.chat_orchestrator = (
            ChatOrchestrator()
        )



    def process(
        self,
        message: str,
        context: dict[str, Any] | None = None
    ):


        context = context or {}


        trace = (
            self.observability
            .start_trace()
        )


        try:


            def _model_generate(prompt: str, context: str = "") -> str:
                """Call native/local weights directly — never re-enter chatgpt_runtime."""
                try:
                    native = None
                    engine = None
                    try:
                        from om_ai.api import main as api_main

                        native = getattr(api_main, "native_backend", None)
                        engine = getattr(api_main, "engine", None)
                    except Exception:
                        native = None
                        engine = None
                    msgs: list[dict[str, str]] = []
                    if context:
                        msgs.append({"role": "system", "content": str(context)[:2000]})
                    msgs.append({"role": "user", "content": str(prompt or "")})

                    native_ready = bool(
                        native is not None
                        and getattr(native, "loaded", False)
                        and getattr(native, "_trained", False)
                        and callable(getattr(native, "chat", None))
                    )
                    if native_ready:
                        try:
                            return str(native.chat(msgs) or "").strip()
                        except Exception:
                            try:
                                return str(native.chat(prompt) or "").strip()
                            except Exception:
                                pass

                    if engine is not None and getattr(engine, "model", None) is not None:
                        chat_fn = getattr(engine, "chat", None)
                        if callable(chat_fn):
                            try:
                                return str(chat_fn(msgs) or "").strip()
                            except Exception:
                                try:
                                    return str(chat_fn(prompt) or "").strip()
                                except Exception:
                                    pass

                    from om_ai.core.intelligence.real_answer import build_real_answer

                    return str(build_real_answer(prompt) or "").strip()
                except Exception:
                    return ""


            def _clean(ans: Any) -> str:
                text = str(ans or "").strip()
                if not text:
                    return ""
                try:
                    from om_ai.core.chat_intelligence.stub_detect import is_solution_stub

                    if is_solution_stub(text):
                        return ""
                except Exception:
                    pass
                try:
                    from om_ai.core.intelligence.real_answer import looks_like_static_reply

                    if looks_like_static_reply(text):
                        return ""
                except Exception:
                    pass
                return text


            # --------------------------------
            # 1. Route request
            # --------------------------------


            route = (
                self.conversation_router
                .route(
                    message,
                    context=context
                )
            )


            self.observability.log(

                trace,

                ActivityEvent(

                    type=ActivityType.THINKING,

                    title="Conversation routing",

                    description=
                    route.get(
                        "reason",
                        ""
                    ),

                    metadata=route

                )

            )


            route_type = (
                route.get(
                    "route"
                )
            )



            # --------------------------------
            # 2. Execute intelligence (full brain + model)
            # --------------------------------


            answer = ""


            if route_type == "emotional":


                answer = _clean(
                    self.emotional_engine
                    .respond(
                        message,
                        context=context
                    )
                )


            elif route_type == "research":


                answer = _clean(
                    self.research_engine
                    .research(
                        message
                    )
                )


            elif route_type == "action":


                answer = _clean(
                    self.action_engine
                    .execute(
                        message,
                        context=context
                    )
                )


            # Default / conversation / problem / coding → full controller + model
            if not answer:
                pack = (
                    self.controller.run(
                        message,
                        model_generate=_model_generate,
                        extra=context,
                    )
                )
                answer = _clean(
                    pack.get("answer")
                    if isinstance(pack, dict)
                    else pack
                )


            if not answer and route_type in ("problem_solving", "coding"):
                result = self.solution_engine.solve(
                    message,
                    context=context,
                    model_generate=_model_generate,
                )
                answer = _clean(result.get("answer") if isinstance(result, dict) else "")


            if not answer:
                try:
                    from om_ai.core.intelligence.real_answer import build_real_answer

                    answer = _clean(build_real_answer(message) or "")
                except Exception:
                    answer = ""


            if not answer:
                answer = (
                    "I'm here with you. Tell me what you need — "
                    "I can help think it through."
                )



            # --------------------------------
            # 3. Safety
            # --------------------------------


            safe = (
                self.safety_filter
                .filter(
                    answer or ""
                )
            )

            answer = (
                safe.get("answer", answer)
                if isinstance(safe, dict)
                else (safe or answer)
            )


            # --------------------------------
            # 4. Quality improve
            # --------------------------------


            answer = (
                self.chat_quality_engine
                .improve(
                    answer or "",
                    question=message
                )
            )



            self.observability.log(

                trace,

                ActivityEvent(

                    type=ActivityType.RESPONSE,

                    title="OM response generated",

                    description=
                    "Human intelligence pipeline completed",

                    metadata={
                        "route":route_type
                    }

                )

            )


            return {


                "trace_id":
                    getattr(
                        trace,
                        "trace_id",
                        None
                    ),


                "answer":
                    answer,


                "route":
                    route,


                "success":
                    True

            }



        except Exception as exc:


            logger.exception(
                "OM Brain failure"
            )


            return {


                "success":
                    False,


                "answer":
                    (
                        "I had trouble processing that. "
                        "Please try again."
                    ),


                "error":
                    str(exc)

            }