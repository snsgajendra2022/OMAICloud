"""
OM Risk Assessment Engine

Analyzes potential danger
before execution.
"""


class RiskAnalyzer:


    HIGH_RISK_ACTIONS = [

        "delete",

        "shutdown",

        "format",

        "unlock",

        "disable security"

    ]


    def analyze(

        self,

        action

    ):


        action_text = action.lower()


        risk="low"


        if any(

            item in action_text

            for item in self.HIGH_RISK_ACTIONS

        ):

            risk="high"



        return {


            "action":

                action,


            "risk":

                risk,


            "approved":

                risk != "high"

        }