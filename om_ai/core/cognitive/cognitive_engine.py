from .reasoning_engine import ReasoningEngine
from .planner import PlanningEngine
from .response_engine import ResponseEngine
from .self_evaluator import SelfEvaluator
from .agent_collaboration import AgentCollaboration
from om_ai.core.knowledge_fusion import KnowledgeFusionEngine
from om_ai.core.agents import AgentManager

class CognitiveEngine:


    def __init__(self):

        self.reasoning = ReasoningEngine()

        self.planner = PlanningEngine()

        self.response = ResponseEngine()

        self.evaluate = SelfEvaluator()

        self.agents = AgentCollaboration()
        self.knowledge = KnowledgeFusionEngine()
        self.agents = AgentManager()



    def process(
        self,
        user_input
    ):


        context={

            "input":
                user_input

        }


        reasoning = self.reasoning.analyze(
            context
        )


        plan = self.planner.create_plan(
            user_input
        )


        agent = self.agents.route(
            user_input
        )

        context = self.knowledge.process(
            user_input
        )

        reasoning = self.reasoning.analyze(
            context
        )
        team = self.agents.create_team(
            user_input
        )

        return {

            "reasoning":
                reasoning,

            "plan":
                plan,
            "context":
                context,

            "reasoning":
                reasoning,
            "agent":
                agent,
            "team":
                team,
        }