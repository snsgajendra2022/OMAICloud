"""
OM Robot Controller
"""


from .motion import MotionPlanner

from .actuator import ActuatorSystem




class RobotController:


    def __init__(self):


        self.motion=MotionPlanner()

        self.actuator=ActuatorSystem()



    def execute(

        self,

        goal

    ):


        plan=self.motion.plan(

            goal

        )


        action=self.actuator.execute(

            plan

        )


        return {


            "plan":

                plan,


            "result":

                action

        }