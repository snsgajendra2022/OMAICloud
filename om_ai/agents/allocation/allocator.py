"""
OM Dynamic Agent Allocation Engine
"""


from .registry import AgentRegistry

from .scorer import AgentScorer





class AgentAllocator:



    def __init__(self):


        self.registry = AgentRegistry()

        self.scorer = AgentScorer()




    def allocate(

        self,

        task:str

    ):


        results=[]



        for agent in self.registry.available():


            results.append(

                self.scorer.score(

                    task,

                    agent

                )

            )



        results.sort(

            key=lambda x:

            x["score"],

            reverse=True

        )



        selected = results[0]



        return {


            "task":

                task,


            "selected_agent":

                selected["agent"],


            "confidence":

                selected["score"],


            "alternatives":

                results[1:]

        }