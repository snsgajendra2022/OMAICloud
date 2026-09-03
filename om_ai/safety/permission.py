"""
OM Permission Management
"""


class PermissionManager:



    def verify(

        self,

        user,

        action

    ):


        return {


            "user":

                user,


            "action":

                action,


            "permission":

                "granted"

        }