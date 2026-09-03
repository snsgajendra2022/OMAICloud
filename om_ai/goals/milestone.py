"""
OM Goal Milestone
"""


from dataclasses import dataclass




@dataclass
class Milestone:


    id: str


    title: str


    status: str = "pending"


    tasks:list = None



    def to_dict(self):

        return {


            "id":

                self.id,


            "title":

                self.title,


            "status":

                self.status,


            "tasks":

                self.tasks or []

        }