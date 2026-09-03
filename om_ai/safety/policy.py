"""
OM Safety Policy Engine
"""


class PolicyEngine:



    def check(

        self,

        action

    ):


        blocked = [

            "bypass security",

            "steal data",

            "harm user"

        ]



        for item in blocked:


            if item in action.lower():

                return {


                    "allowed":

                        False,


                    "reason":

                        item

                }



        return {


            "allowed":

                True

        }