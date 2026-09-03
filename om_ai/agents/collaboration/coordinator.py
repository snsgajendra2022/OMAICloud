"""
OM Multi Agent Coordinator

Executes multiple agents together.
"""


from __future__ import annotations


from om_ai.agents.coding_agent import CodingAgent

from om_ai.agents.research_agent import ResearchAgent
from om_ai.agents.coding_agent import CodingAgent
from om_ai.agents.research_agent import ResearchAgent
from om_ai.agents.database_agent import DatabaseAgent
from om_ai.agents.business_agent import BusinessAgent
from om_ai.agents.memory_agent import MemoryAgent


class AgentCoordinator:



    def __init__(self):


        self.available_agents={


        "coding":
            CodingAgent(),


        "research":
            ResearchAgent(),

        "coding":
            CodingAgent(),


        "research":
            ResearchAgent(),


        "database":
            DatabaseAgent(),


        "business":
            BusinessAgent(),


        "memory":
            MemoryAgent()

        }



    def execute(
        self,
        agent_plan:list[str],
        question:str,
        context=None
    ):


        results=[]



        for name in agent_plan:


            agent = self.available_agents.get(
                name
            )


            if not agent:

                results.append(

                    {

                        "agent":name,

                        "status":"not_available"

                    }

                )

                continue



            result = agent.execute(

                question,

                context

            )


            results.append(

                result

            )



        return results