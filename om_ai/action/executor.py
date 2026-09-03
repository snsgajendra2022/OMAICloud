"""
OM Autonomous Tool Executor
"""


from .registry import ToolRegistry
from om_ai.security import SecurityController




class ToolExecutor:



    def __init__(self):


        self.registry = ToolRegistry()
        self.security = SecurityController()



    def register_tool(

        self,

        tool

    ):


        self.registry.register(
            tool
        )




    def execute(

        self,

        tool_name:str,

        **kwargs

    ):


        tool=self.registry.get(

            tool_name

        )


        if not tool:


            return {


                "success":

                    False,


                "error":

                    "tool not found"

            }



        try:


            result=self.security.execute(
                    agent="tool_executor",
                    action=tool.description,
                    resource=tool.name,
                    function=tool.function,
                    **kwargs
                )

            return {
                "success":

                    True,
                "result":
                    result
            }


        except Exception as e:


            return {


                "success":

                    False,


                "error":

                    str(e)

            }