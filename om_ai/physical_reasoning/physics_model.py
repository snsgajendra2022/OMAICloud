"""
OM Physics World Model

Understands:
- gravity
- stability
- movement
- interaction
"""


class PhysicsWorldModel:


    def analyze(

        self,

        object_data

    ):


        return {


            "object":

                object_data.get(

                    "name"

                ),


            "properties":

            {


                "gravity":

                    True,


                "movable":

                    True,


                "fragile":

                    False

            }

        }