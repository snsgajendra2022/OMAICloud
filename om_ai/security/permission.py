"""
OM Permission Manager
"""





class PermissionManager:



    def __init__(self):


        self.permissions={}




    def grant(

        self,

        agent:str,

        permission:str

    ):


        self.permissions.setdefault(

            agent,

            []

        )


        self.permissions[agent].append(

            permission

        )




    def check(

        self,

        agent:str,

        permission:str

    ):


        return permission in self.permissions.get(

            agent,

            []

        )