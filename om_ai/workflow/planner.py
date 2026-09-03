"""
OM Dynamic Workflow Planner
"""


class WorkflowPlanner:



    def plan(

        self,

        tasks:list

    ):


        for index, task in enumerate(tasks):


            if index > 0:


                task["dependency"]=[

                    tasks[index-1]["id"]

                ]

            else:

                task["dependency"]=[]



        return tasks