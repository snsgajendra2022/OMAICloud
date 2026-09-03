"""
OM Safety Decision Engine
"""


class SafetyDecision:



    def decide(

        self,

        risk,

        policy

    ):


        if not policy["allowed"]:

            return {

                "decision":

                    "blocked"

            }



        if risk["risk"] == "high":

            return {

                "decision":

                    "requires_approval"

            }



        return {

            "decision":

                "approved"

        }