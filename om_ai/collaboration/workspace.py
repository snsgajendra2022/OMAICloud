"""
OM Shared Agent Workspace
"""


class AgentWorkspace:



    def __init__(self):

        self.data={}




    def write(

        self,

        key:str,

        value

    ):


        self.data[key]=value



        return True




    def read(

        self,

        key:str,

        default=None

    ):


        return self.data.get(

            key,

            default

        )




    def all(self):


        return self.data