"""
OM Autonomous Tool Executor
"""


from .registry import ToolRegistry
from om_ai.security import SecurityController
from om_ai.observability import OMMonitor



class ToolExecutor:



    def __init__(self):


        self.registry = ToolRegistry()
        self.security = SecurityController()
        self.monitor = OMMonitor()


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
            self.monitor.execution_started(

                    agent="tool_executor"

                )
            if result.get("success"):

                self.monitor.metrics.increment(
                    "successful_actions"
                )

            else:

                self.monitor.execution_failed(
                    result.get("error")
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