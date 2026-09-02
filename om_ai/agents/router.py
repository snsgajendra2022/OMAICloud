"""
OM Agent Router

Selects best agent.
"""


from .coding_agent import CodingAgent

from .research_agent import ResearchAgent

from .general_agent import GeneralAgent





class AgentRouter:



    def __init__(self):

        self.agents=[

            CodingAgent(),

            ResearchAgent(),

            GeneralAgent()

        ]



    def route(
        self,
        question:str
    ):


        results=[]


        for agent in self.agents:


            score=agent.can_handle(
                question
            )


            results.append(

                {

                    "agent":agent,

                    "score":score

                }

            )



        results.sort(

            key=lambda x:x["score"],

            reverse=True

        )


        selected=results[0]



        return {

            "agent":
                selected["agent"],

            "name":
                selected["agent"].name,

            "score":
                selected["score"]

        }