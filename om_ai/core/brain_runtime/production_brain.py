from __future__ import annotations

import logging


from om_ai.core.observability import (
    ObservabilityEngine,
    ActivityEvent,
    ActivityType,
)


from om_ai.core.knowledge_brain import (
    KnowledgeBrain,
)


from om_ai.core.long_context import (
    LongContextEngine,
)


from om_ai.core.advanced_reasoning import (
    ReasoningEngine,
)



logger = logging.getLogger(
    "OMProductionBrain"
)



class OMProductionBrain:
    """
    Main OM AI production brain.

    Responsible for:

    - context handling
    - knowledge lookup
    - reasoning
    - activity tracing
    - future agent integration

    """


    def __init__(self):


        self.observability = (
            ObservabilityEngine()
        )


        self.knowledge_brain = (
            KnowledgeBrain()
        )


        self.context_engine = (
            LongContextEngine()
        )


        self.reasoning_engine = (
            ReasoningEngine()
        )



    def process(
        self,
        message: str
    ):


        #
        # Create trace
        #

        trace = (
            self.observability
            .start_trace()
        )



        self.observability.log(

            trace,

            ActivityEvent(

                ActivityType.USER_REQUEST,

                "Processing user request",

                metadata={
                    "message_length":
                    len(message)
                }

            )

        )



        #
        # Context
        #

        context = (
            self.context_engine
            .process(
                message
            )
        )


        self.observability.log(

            trace,

            ActivityEvent(

                ActivityType.MEMORY_ACCESS,

                "Loading conversation context",

            )

        )



        #
        # Knowledge Brain
        #

        knowledge = (
            self.knowledge_brain
            .analyze(
                message
            )
        )



        self.observability.log(

            trace,

            ActivityEvent(

                ActivityType.KNOWLEDGE_LOOKUP,

                "Checking OM knowledge brain",

                metadata={

                    "query":
                    message,

                    "confidence":
                    knowledge.confidence

                }

            )

        )



        #
        # Reasoning
        #

        reasoning = (
            self.reasoning_engine
            .reason(
                message
            )
        )


        self.observability.log(

            trace,

            ActivityEvent(

                ActivityType.AGENT_START,

                "Reasoning engine started"

            )

        )



        #
        # Response placeholder
        #
        # Actual response engine
        # will connect here
        #

        answer = {

            "message":
            message,

            "context":
            context,

            "knowledge":
            knowledge,

            "reasoning":
            reasoning

        }



        self.observability.log(

            trace,

            ActivityEvent(

                ActivityType.RESPONSE,

                "Response generated",

                metadata={

                    "status":
                    "success"

                }

            )

        )



        return {


            "trace_id":

            trace.trace_id,


            "response":

            answer

        }