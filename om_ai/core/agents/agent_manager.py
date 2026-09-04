from .agent_registry import AgentRegistry
from .team_builder import TeamBuilder



class AgentManager:


    def __init__(self):

        self.registry = AgentRegistry()

        self.team_builder = TeamBuilder()



    def create_team(
        self,
        task
    ):

        return self.team_builder.create_team(
            task
        )



    def available_agents(self):

        return self.registry.list_agents()