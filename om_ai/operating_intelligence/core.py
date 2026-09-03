"""
OM Operating Intelligence Core

Central brain coordinator.
"""


class OMCore:


    def __init__(self):

        self.modules = {}



    def register(

        self,

        name,

        module

    ):


        self.modules[name] = module



    def get(

        self,

        name

    ):


        return self.modules.get(

            name

        )



    def list_modules(self):


        return list(

            self.modules.keys()

        )