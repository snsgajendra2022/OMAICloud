from .mission import Mission
from .mission_planner import MissionPlanner
from .task_delegator import TaskDelegator



class CivilizationEngine:


    def __init__(self):

        self.planner = MissionPlanner()

        self.delegator = TaskDelegator()



    def create_mission(
        self,
        goal
    ):


        tasks = self.planner.create(
            goal
        )


        return Mission(

            goal=goal,

            tasks=tasks

        )



    def assign_tasks(
        self,
        mission
    ):


        assignments=[]


        for task in mission.tasks:


            agent = (
                self.delegator.assign(
                    task,
                    []
                )
            )


            assignments.append({

                "task":
                task,

                "agent":
                agent

            })


        return assignments