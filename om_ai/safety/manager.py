"""
OM Advanced Safety Manager
"""


from .risk import RiskAnalyzer

from .policy import PolicyEngine

from .permission import PermissionManager

from .alignment import AlignmentChecker

from .decision import SafetyDecision

from .audit import SafetyAudit

from .memory import SafetyMemory





class SafetyManager:



    def __init__(self):


        self.risk=RiskAnalyzer()

        self.policy=PolicyEngine()

        self.permission=PermissionManager()

        self.alignment=AlignmentChecker()

        self.decision=SafetyDecision()

        self.audit=SafetyAudit()

        self.memory=SafetyMemory()



    def validate(

        self,

        action,

        user="system"

    ):


        risk=self.risk.analyze(

            action

        )


        policy=self.policy.check(

            action

        )


        permission=self.permission.verify(

            user,

            action

        )


        alignment=self.alignment.evaluate(

            "OM objectives",

            action

        )


        decision=self.decision.decide(

            risk,

            policy

        )


        result={


            "risk":

                risk,


            "policy":

                policy,


            "permission":

                permission,


            "alignment":

                alignment,


            "decision":

                decision

        }



        self.audit.record(

            result

        )


        self.memory.remember(

            result

        )


        return result