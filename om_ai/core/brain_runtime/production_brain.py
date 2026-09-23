# from __future__ import annotations

# import logging

# from om_ai.core.chatgpt_runtime import OMBrainController, run_chatgpt_runtime
# from om_ai.core.observability import (
#     ActivityEvent,
#     ActivityType,
#     ObservabilityEngine,
# )
# from om_ai.core.chat_intelligence import ConversationRouter
# from om_ai.core.chat_intelligence import CodingEngine
# from om_ai.core.chat_intelligence import ResearchEngine
# from om_ai.core.chat_intelligence import EmotionalEngine
# from om_ai.core.chat_intelligence import ActionEngine
# from om_ai.core.chat_intelligence import SolutionPlanner
# from om_ai.core.chat_intelligence import UserPreference
# from om_ai.core.chat_intelligence import VerificationEngine
# from om_ai.core.chat_intelligence import AnswerPlanner
# from om_ai.core.chat_intelligence import ChatOrchestrator
# from om_ai.core.chat_intelligence import ChatQualityEngine
# from om_ai.core.chat_intelligence import ProblemAnalyzer
# from om_ai.core.chat_intelligence import ReasoningEngine
# from om_ai.core.chat_intelligence import ResponseOptimizer
# from om_ai.core.chat_intelligence import SafetyFilter
# from om_ai.core.chat_intelligence import SolutionEngine
# from om_ai.core.chat_intelligence import SolutionMemory


# logger = logging.getLogger("OMProductionBrain")


# class OMProductionBrain:
#     """
#     Production brain front door — STEP 30 ChatGPT-like controller.

#     User → Chat Intelligence → Brain Router → Response Intelligence → Answer
#     """

#     def __init__(self) -> None:
#         self.observability = ObservabilityEngine()
#         self.controller = OMBrainController()
#         self.conversation_router = ConversationRouter()
#         self.coding_engine = CodingEngine()
#         self.research_engine = ResearchEngine()
#         self.emotional_engine = EmotionalEngine()
#         self.action_engine = ActionEngine()
#         self.solution_planner = SolutionPlanner()
#         self.user_preference = UserPreference()
#         self.verification_engine = VerificationEngine()
#         self.answer_planner = AnswerPlanner()
#         self.chat_orchestrator = ChatOrchestrator()
#         self.chat_quality_engine = ChatQualityEngine()
#         self.problem_analyzer = ProblemAnalyzer()
#         self.reasoning_engine = ReasoningEngine()
#         self.response_optimizer = ResponseOptimizer()
#         self.safety_filter = SafetyFilter()
#         self.solution_engine = SolutionEngine()
#         self.solution_memory = SolutionMemory()
    
#     def process(self, message: str):
#         trace = self.observability.start_trace()
#         self.observability.log(
#             trace,
#             ActivityEvent(
#                 type=ActivityType.THINKING,
#                 title="Processing user request",
#                 description="STEP 30 OM Brain Controller",
#                 metadata={"message_length": len(message or "")},
#             ),
#         )

#         pack = (
#             self.controller.run(message)
#             if self.controller
#             else run_chatgpt_runtime(message)
#         )

#         self.observability.log(
#             trace,
#             ActivityEvent(
#                 type=ActivityType.RESPONSE,
#                 title="ChatGPT-like runtime completed",
#                 description="Understand → Solve → Improve → Answer",
#                 metadata={
#                     "source": pack.get("source"),
#                     "stages": list(pack.get("stages") or [])[:12],
#                 },
#             ),
#         )

#         return {
#             "trace_id": getattr(trace, "trace_id", None),
#             "response": pack,
#             "answer": pack.get("answer") or "",
#             "context_blob": pack.get("context_blob") or "",
#             "meta": pack.get("meta") or {},
#             "stages": pack.get("stages") or [],
#             "chat_intelligence": pack.get("chat_intelligence") or {},
#         }
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
            # 2. Execute intelligence
            # --------------------------------


            if route_type == "emotional":


                answer = (
                    self.emotional_engine
                    .respond(
                        message,
                        context=context
                    )
                )


            elif route_type == "conversation":


                pack = (
                    self.chat_orchestrator
                    .run(
                        message,
                        extra=context
                    )
                )

                answer = (
                    pack.get(
                        "answer"
                    )
                    if isinstance(pack, dict)
                    else str(pack or "")
                )


            elif route_type in (
                "problem_solving",
                "coding"
            ):


                result = (
                    self.solution_engine
                    .solve(
                        message,
                        context=context
                    )
                )


                answer = (
                    result.get(
                        "answer"
                    )
                )



            elif route_type == "research":


                answer = (
                    self.research_engine
                    .research(
                        message
                    )
                )


            elif route_type == "action":


                answer = (
                    self.action_engine
                    .execute(
                        message,
                        context=context
                    )
                )


            else:


                pack = (
                    self.controller.run(
                        message
                    )
                )

                answer = (
                    pack.get(
                        "answer"
                    )
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