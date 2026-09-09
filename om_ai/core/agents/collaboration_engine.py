from .agent_registry import AgentRegistry
from .agent_router import AgentRouter



class CollaborationEngine:


    def __init__(self):

        self.registry = AgentRegistry()

        self.router = AgentRouter()



    def register_agent(
        self,
        agent
    ):

        self.registry.register(
            agent
        )



    def execute(
        self,
        task,
        understanding,
        reasoning
    ):


        selected = self.router.select(
            understanding,
            reasoning
        )


        results=[]


        for agent_name in selected:


            agent = (
                self.registry.get(
                    agent_name
                )
            )


            if agent:


                result = agent.execute(
                    task,
                    {
                        "understanding":
                            understanding,

                        "reasoning":
                            reasoning
                    }
                )


                results.append(
                    result
                )


        return results