"""
OM-1.0 Cognitive Brain — facade over the existing reasoning pipeline.

Features:

- Memory System
- Agent Router
- Intent Understanding
- Technology Detection
- Reasoning Engine
- Answer Generation
- Evaluation

Usage:

OMCognitiveBrain().process(
    "create react native login and dashboard app"
)

"""


from __future__ import annotations


from typing import Any


from om_ai.memory import MemoryManager

from om_ai.agents import (
    AgentRouter,
    AgentExecutor
)

from om_ai.cognition.intent_engine import IntentEngine

from om_ai.learning import LearningEngine
from om_ai.orchestration import OMOrchestrator
from om_ai.cognition.task_planner import TaskPlanner
from om_ai.evaluation.self_checker import SelfEvaluator
from om_ai.improvement import KnowledgeImprovementEngine
from om_ai.cognition.technology_engine import TechnologyEngine
from om_ai.core.reasoning.reasoning_chain import ReasoningChain
from om_ai.core.response.answer_generator import AnswerGenerator

from om_ai.understanding.query_kind import (
    is_coding_task,
    is_greeting,
    query_kind
)
from om_ai.agents.collaboration import (
    AgentCollaborationPlanner,
    AgentCoordinator
)




class OMCognitiveBrain:



    def __init__(self) -> None:

        self.memory = MemoryManager()
        self.intent = IntentEngine()
        self.technology = TechnologyEngine()
        self.planner = TaskPlanner()
        self.reasoning = ReasoningChain()
        self.generator = AnswerGenerator()
        self.evaluator = SelfEvaluator()
        self.agent_router = AgentRouter()
        self.agent_executor = AgentExecutor()
        self.agent_planner = AgentCollaborationPlanner()
        self.agent_coordinator = AgentCoordinator()
        self.learning = LearningEngine()
        self.improvement = KnowledgeImprovementEngine()
        self.orchestrator = OMOrchestrator()

    def process(
        self,
        question: str,
        knowledge: Any = None
    ) -> dict[str, Any]:


        question = (
            question or ""
        ).strip()

        # ----------------------------
        # Agent Routing
        # ----------------------------

        agent_result = self.agent_router.route(
            question
        )

        # ----------------------------
        # Memory Retrieval
        # ----------------------------

        existing_memory = self.memory.get_context()



        relevant_memory = self.memory.get_relevant_memory(

            question,

            memories=existing_memory

        )
        memory_context = {
            "relevant":relevant_memory
            
        }

        orchestration = self.orchestrator.orchestrate(

            question,

            agent_result,

            memory=memory_context,

            knowledge=knowledge,

        )
        agent_plan = self.agent_planner.plan(
            question
        )

        agent_team_result = self.agent_coordinator.execute(

            agent_plan,

            question,

            {
                "memory":memory_context
            }

        )
        

        agent_execution = self.agent_executor.execute(

            agent_result,

            question,

            {

                "memory": memory_context

            }

        )
        # ----------------------------
        # Empty Question
        # ----------------------------

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
                    "issues":[
                        "empty question"
                    ]

                }

            }



        # ----------------------------
        # Query Type
        # ----------------------------

        kind = query_kind(
            question
        )
        # ----------------------------
        # Intent
        # ----------------------------

        intent_result = self.intent.analyze(
            question
        )


        # ----------------------------
        # Technology
        # ----------------------------

        if is_coding_task(question):

            technology_result = self.technology.analyze(
                question
            )

        else:

            technology_result = {

                "technology":None,

                "category":"unknown",

                "language":None,

                "platform":None,

                "confidence":0


            }





        # ----------------------------
        # Task Planning
        # ----------------------------

        task_result = self.planner.decompose(
            question
        )



        if kind in {
            "greeting",
            "knowledge"
        }:


            task_result = {


                "goal":question,

                "category":"general",

                "tasks":[]


            }



        # ----------------------------
        # External Knowledge
        # ----------------------------

        hits = None



        if kind == "greeting":


            hits=[]



        elif isinstance(
            knowledge,
            list
        ):


            hits=[

                str(x).strip()

                for x in knowledge

                if str(x).strip()

            ]



        elif isinstance(
            knowledge,
            dict
        ):


            text = str(

                knowledge.get(
                    "text"
                )
                or
                knowledge.get(
                    "answer"
                )
                or ""

            ).strip()



            hits=[text] if text else None



        elif isinstance(
            knowledge,
            str
        ) and knowledge.strip():


            hits=[

                knowledge.strip()

            ]





        # ----------------------------
        # Main Reasoning Pipeline
        # ----------------------------

        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline



        pipeline = run_reasoning_pipeline(

            question,

            knowledge_hits=hits,

            retrieve=not hits and kind != "greeting",

            messages=None

        )

        pipeline["agent"] = agent_result
        pipeline["agent_execution"] = agent_execution
        pipeline["agent_plan"] = agent_plan
        pipeline["agent_team"] = agent_team_result
        pipeline["orchestration"] = orchestration



        generated = None



        user_answer = str(

            pipeline.get(
                "user_response"
            )
            or
            pipeline.get(
                "answer"
            )
            or ""

        ).strip()



        # ----------------------------
        # Fallback Reasoning
        # ----------------------------

        if not user_answer:


            reasoning_result = self.reasoning.analyze(
                question,
                intent=intent_result,
                technology=technology_result,
                tasks=task_result,
                knowledge=knowledge,
                memory=memory_context,
                agent_result=agent_result,
                agent_execution=agent_execution,
                agent_team=agent_team_result
            )



            generated = self.generator.generate(

                question,

                reasoning_result,

                knowledge

            )



            if isinstance(
                generated,
                dict
            ):


                user_answer = str(

                    generated.get(
                        "answer",
                        ""

                    )

                ).strip()



            else:


                user_answer = str(
                    generated
                ).strip()





        # ----------------------------
        # Save Memory
        # ----------------------------

        self.memory.remember_conversation(

            question,

            user_answer

        )



        # ----------------------------
        # Evaluation
        # ----------------------------

        evaluation = pipeline.get(
            "evaluation"
        )



        if not evaluation:


            evaluation = self.evaluator.evaluate(

                question,

                user_answer,

                technology_result

            )


        improvement_result = self.improvement.improve(

                question,

                user_answer,

                evaluation

            )
        # ----------------------------
        # Long Term Learning
        # ----------------------------

        learning_result = self.learning.learn(

            question,

            user_answer,

            evaluation

        )

        # ----------------------------
        # Final Response
        # ----------------------------

        from om_ai.core.response.response_formatter import (
            ResponseFormatter,
            response_mode
        )



        formatter = ResponseFormatter()



        payload = {


            "question":
                question,


            "intent":
                pipeline.get(
                    "intent"
                )
                or intent_result,


            "technology":
                pipeline.get(
                    "technology"
                )
                or technology_result,


            "tasks":
                task_result,


            "reasoning":
                pipeline,


            "answer":
                user_answer,


            "evaluation":
                evaluation,


            "memory":
                memory_context,


            "agent":
                agent_result,
            "evaluation":
                evaluation,
            "learning":
                learning_result,
            "improvement":
                improvement_result,
            "orchestration": orchestration,

        }



        user_response = formatter.format_user_response(
            payload
        )



        developer_response = formatter.format_developer_response(
            payload
        )



        visible = (

            developer_response

            if response_mode()=="developer"

            else user_response

        )





        return {


            "answer":
                visible,


            "user_response":
                user_response,


            "developer_response":
                developer_response,


            "agent":
                agent_result,


            "memory":
                memory_context,


            "intent":
                payload["intent"],


            "technology":
                payload["technology"],


            "tasks":
                task_result,


            "reasoning":
                pipeline,


            "evaluation":
                evaluation,


            "debug":{


                "agent":
                    agent_result,


                "memory":
                    memory_context,


                "evaluation":
                    evaluation,

                "learning":
                    learning_result,
            }


        }