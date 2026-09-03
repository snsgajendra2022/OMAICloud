"""
OM Security Policy Engine

Defines allowed and blocked actions.
"""



class SecurityPolicy:



    def __init__(self):


        self.blocked = [

            "rm -rf",

            "format",

            "shutdown",

            "delete database"

        ]


        self.allowed = [

            "read",

            "write",

            "create",

            "test"

        ]




    def check(

        self,

        action:str

    ):


        value = action.lower()



        for item in self.blocked:


            if item in value:


                return {


                    "allowed":False,


                    "reason":

                    "blocked operation"

                }




        return {


            "allowed":True,


            "reason":

            "policy passed"

        }