"""
OM Human-Level Physical Reasoning Manager
"""


from .physics_model import PhysicsWorldModel

from .object_state import ObjectStateEngine

from .relation_engine import RelationEngine

from .causal_reasoning import CausalReasoning

from .prediction_engine import PredictionEngine

from .decision import PhysicalDecision

from .memory import PhysicalMemory





class PhysicalReasoningManager:


    def __init__(self):


        self.physics = PhysicsWorldModel()

        self.objects = ObjectStateEngine()

        self.relations = RelationEngine()

        self.causal = CausalReasoning()

        self.prediction = PredictionEngine()

        self.decision = PhysicalDecision()

        self.memory = PhysicalMemory()



    def analyze(

        self,

        environment

    ):


        physics=self.physics.analyze(

            environment

        )


        state=self.objects.analyze(

            environment.get(

                "object"

            )

        )


        relation=self.relations.understand(

            environment.get(

                "objects",

                []

            )

        )


        cause=self.causal.predict(

            environment.get(

                "action"

            )

        )


        future=self.prediction.predict(

            state

        )


        decision=self.decision.decide(

            future

        )


        result={


            "physics":

                physics,


            "state":

                state,


            "relations":

                relation,


            "cause_effect":

                cause,


            "future":

                future,


            "decision":

                decision

        }


        self.memory.store(

            result

        )


        return result