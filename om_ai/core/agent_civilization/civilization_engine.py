from .agent_registry import AgentRegistry
from .collaboration_manager import CollaborationManager
from .agent_evaluator import AgentEvaluator



class CivilizationEngine:


    def __init__(self):

        self.registry=AgentRegistry()

        self.collaboration=CollaborationManager()

        self.evaluator=AgentEvaluator()



    def add_agent(
        self,
        profile
    ):

        self.registry.register(
            profile
        )



    def execute(
        self,
        task
    ):


        agents=list(
            self.registry.all()
            .values()
        )


        result=self.collaboration.collaborate(
            agents,
            task
        )


        return {

            "results":

                result,


            "evaluation":

                self.evaluator.evaluate(
                    result
                )

        }