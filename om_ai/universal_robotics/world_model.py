"""
OM Universal Robotics World Model
"""


class WorldModel:


    def __init__(self):

        self.environment = {}



    def update(

        self,

        observation

    ):


        self.environment.update(

            observation

        )


        return self.environment



    def understand(self):


        return {


            "objects":

                list(

                    self.environment.keys()

                ),


            "status":

                "understanding"

        }