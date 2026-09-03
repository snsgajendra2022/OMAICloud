"""
OM Robotics Intelligence Manager
"""


from .controller import RobotController

from .learning import RobotLearning



class RoboticsManager:


    def __init__(self):

        self.controller=RobotController()

        self.learning=RobotLearning()



    def execute(

        self,

        goal

    ):


        result=self.controller.execute(

            goal

        )


        self.learning.learn(

            result

        )


        return result