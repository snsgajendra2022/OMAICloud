"""
OM Agent Shared Memory
"""





class AgentMemory:



    def __init__(self):

        self.memory=[]




    def store(

        self,

        agent,

        information

    ):


        self.memory.append(

            {

                "agent":

                    agent,


                "information":

                    information

            }

        )




    def search(

        self,

        keyword

    ):


        return [

            item

            for item in self.memory

            if keyword.lower()

            in str(item).lower()

        ]