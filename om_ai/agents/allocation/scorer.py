"""
OM Agent Selection Scoring
"""



class AgentScorer:



    def score(

        self,

        task,

        agent

    ):


        return {

            "agent":

                agent.name,


            "score":

                agent.matches(task)

        }