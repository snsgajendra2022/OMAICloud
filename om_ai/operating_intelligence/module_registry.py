"""
OM Intelligence Module Registry
"""


class ModuleRegistry:



    def __init__(self):


        self.registry = {}



    def add(

        self,

        name,

        status="active"

    ):


        self.registry[name] = {


            "status":

                status

        }



    def all(self):


        return self.registry