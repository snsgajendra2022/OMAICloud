"""
OM Autonomous Goal Manager
"""


import uuid


from .storage import GoalStorage

from .progress import GoalProgress





class GoalManager:



    def __init__(self):


        self.storage=GoalStorage()

        self.progress=GoalProgress()




    def create_goal(

        self,

        title:str,

        description:str,

        milestones:list

    ):


        goal={


            "id":

                uuid.uuid4().hex,


            "title":

                title,


            "description":

                description,


            "status":

                "active",


            "progress":

                0,


            "milestones":

                milestones

        }



        self.storage.add(

            goal

        )


        return goal





    def update(

        self,

        goal_id,

        milestones

    ):


        goals=self.storage.load()



        for goal in goals:


            if goal["id"] == goal_id:


                goal["milestones"]=milestones


                goal["progress"]=self.progress.calculate(

                    milestones

                )



        self.storage.save(

            goals

        )


        return goals