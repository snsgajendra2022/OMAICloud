"""
OM Tool Safety Manager

Controls tool execution.
"""


from .permission import PermissionChecker

from .validator import ToolValidator





class ToolSafetyManager:



    def __init__(self):


        self.permission = PermissionChecker()

        self.validator = ToolValidator()




    def check(

        self,

        tool_name:str,

        request:str

    ):


        validation = self.validator.validate(
            request
        )


        if not validation["safe"]:


            return {


                "approved":

                    False,


                "reason":

                    validation["reason"]

            }



        permission = self.permission.check(

            tool_name,

            request

        )



        return {


            "approved":

                permission["allowed"],


            "reason":

                permission["reason"]

        }