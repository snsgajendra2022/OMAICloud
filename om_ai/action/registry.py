"""
OM Tool Registry

Stores available tools.
"""


from .tool import Tool





class ToolRegistry:



    def __init__(self):

        self.tools={}




    def register(

        self,

        tool:Tool

    ):


        self.tools[tool.name]=tool




    def get(

        self,

        name:str

    ):


        return self.tools.get(
            name
        )




    def all(self):


        return list(

            self.tools.keys()

        )