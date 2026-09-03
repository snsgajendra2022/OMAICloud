"""
OM Digital Twin State Manager
"""


from datetime import datetime



class TwinState:



    def create(

        self,

        entity,

        values

    ):


        return {


            "entity":

                entity,


            "state":

                values,


            "timestamp":

                datetime.utcnow().isoformat()

        }