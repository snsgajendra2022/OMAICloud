"""
OM Device Safety Permission Layer
"""


class DevicePermission:



    def check(

        self,

        command

    ):


        dangerous=[

            "shutdown",

            "delete",

            "unlock"

        ]



        if command.action in dangerous:


            return {


                "allowed":

                    False,


                "reason":

                    "Requires approval"

            }



        return {


            "allowed":

                True

        }