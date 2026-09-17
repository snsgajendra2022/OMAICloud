from __future__ import annotations


from .agent_model import AgentResult



class BaseAgent:
    """
    Base OM Agent.
    """


    name = "base"



    def __init__(self):

        self.memory=[]



    def remember(
        self,
        item
    ):

        self.memory.append(
            item
        )



    def execute(
        self,
        task: dict
    ) -> AgentResult:


        raise NotImplementedError