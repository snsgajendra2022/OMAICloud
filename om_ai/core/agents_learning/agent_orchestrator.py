from .agent_registry import AgentRegistry



class AgentOrchestrator:
    """
    Coordinates OM agents.
    """


    def __init__(
        self
    ):

        self.registry = AgentRegistry()



    def register(
        self,
        agent
    ):

        self.registry.register(
            agent
        )



    def run(
        self,
        task
    ):


        results=[]


        for agent in self.registry.all().values():


            result = agent.execute(
                task
            )


            results.append(
                result
            )


        return results