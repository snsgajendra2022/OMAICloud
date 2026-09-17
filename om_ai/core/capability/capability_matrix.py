from __future__ import annotations



class CapabilityMatrix:
    """
    Complete OM intelligence map.
    """


    def __init__(
        self,
        registry
    ):

        self.registry = registry



    def snapshot(self):

        result = {}


        for name, capability in (
            self.registry.all().items()
        ):

            result[name] = {

                "score":
                    round(
                        capability.score * 100,
                        2
                    ),

                "confidence":
                    round(
                        capability.confidence,
                        2
                    ),

                "evaluations":
                    capability.evaluations

            }


        return result



    def weakest(
        self
    ):


        items = list(
            self.registry
            .all()
            .values()
        )


        if not items:

            return None



        return min(
            items,
            key=lambda x: x.score
        )