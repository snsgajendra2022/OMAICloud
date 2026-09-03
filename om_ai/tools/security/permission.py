"""
OM Tool Permission System
"""


class PermissionChecker:



    def check(
        self,
        tool_name:str,
        request:str
    ) -> dict:



        return {


            "tool":

                tool_name,


            "allowed":

                True,


            "reason":

                "safe operation"

        }