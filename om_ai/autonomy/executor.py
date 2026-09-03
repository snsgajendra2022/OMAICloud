"""
OM Autonomous Executor
"""


from .task_queue import TaskQueue
from om_ai.autonomy.evaluation import SelfCorrectionLoop




class AutonomousExecutor:



    def __init__(self):

        self.queue=TaskQueue()
        self.self_checker = SelfCorrectionLoop()


    def load(
        self,
        tasks:list[str]
    ):


        for task in tasks:

            self.queue.add(task)



    def execute_next(self):


        task=self.queue.next()


        if not task:

            return {

                "status":"completed"

            }



        execution = {
            "status":"running",
            "task":task
          }
        review = self.self_checker.review(
            str(execution)
        )
        return {
            **execution,
            "review":review
        }
        