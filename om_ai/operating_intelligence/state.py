"""
OM Global Intelligence State
"""


from datetime import datetime



class OMState:



    def __init__(self):


        self.state = {


            "status":

                "running",


            "started":

                datetime.utcnow().isoformat()

        }



    def update(

        self,

        key,

        value

    ):


        self.state[key] = value



    def get(self):


        return self.state