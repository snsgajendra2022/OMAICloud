"""
OM Workflow Task
"""


from dataclasses import dataclass





@dataclass
class WorkflowTask:


    id: str


    title: str


    agent: str = "general"


    status: str = "pending"


    dependency: list = None



    def to_dict(self):

        return {


            "id":

                self.id,


            "title":

                self.title,


            "agent":

                self.agent,


            "status":

                self.status,


            "dependency":

                self.dependency or []

        }