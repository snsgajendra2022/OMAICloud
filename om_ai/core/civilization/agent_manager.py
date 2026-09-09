class AgentManager:


    def __init__(self):

        self.agents={}



    def register(
        self,
        agent
    ):

        self.agents[
            agent.name
        ] = agent



    def get(
        self,
        name
    ):

        return self.agents.get(name)



    def list_agents(
        self
    ):

        return list(
            self.agents.values()
        )