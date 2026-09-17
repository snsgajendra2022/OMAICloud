from __future__ import annotations


from .capability_model import CapabilityScore



class CapabilityRegistry:
    """
    Stores OM capability profiles.
    """


    def __init__(self):

        self.capabilities = {}



    def register(
        self,
        name: str
    ):

        if name not in self.capabilities:

            self.capabilities[name] = CapabilityScore(
                name=name
            )



    def get(
        self,
        name: str
    ):

        return self.capabilities.get(
            name
        )



    def all(self):

        return self.capabilities