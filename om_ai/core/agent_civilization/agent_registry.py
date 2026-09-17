class AgentRegistry:


    def __init__(self):

        self.agents={}



    def register(
        self,
        profile
    ):


        self.agents[
            profile.identity.agent_id
        ] = profile



    def get(
        self,
        agent_id
    ):

        return self.agents.get(
            agent_id
        )



    def all(self):

        return self.agents