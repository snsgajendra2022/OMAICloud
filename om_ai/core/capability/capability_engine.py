from __future__ import annotations


from .capability_registry import (
    CapabilityRegistry,
)

from .capability_evaluator import (
    CapabilityEvaluator,
)

from .capability_matrix import (
    CapabilityMatrix,
)

from .capability_history import (
    CapabilityHistory,
)



class CapabilityEngine:
    """
    OM Capability Intelligence Engine.

    Measures:

    - Coding
    - Reasoning
    - Planning
    - Research
    - Memory
    - Tool usage

    """


    def __init__(self):

        self.registry = CapabilityRegistry()

        self.evaluator = CapabilityEvaluator()

        self.matrix = CapabilityMatrix(
            self.registry
        )

        self.history = CapabilityHistory()



    def observe(
        self,
        capability: str,
        quality: float,
        success: bool
    ):


        self.registry.register(
            capability
        )


        score = self.evaluator.evaluate(

            quality,

            success

        )


        item = self.registry.get(
            capability
        )


        item.update(
            score
        )


        snapshot = (
            self.matrix.snapshot()
        )


        self.history.add(
            snapshot
        )


        return snapshot



    def profile(self):

        return self.matrix.snapshot()



    def weakest_area(self):

        weakest = self.matrix.weakest()


        if weakest:

            return {

                "capability":
                    weakest.name,

                "score":
                    weakest.score

            }


        return None