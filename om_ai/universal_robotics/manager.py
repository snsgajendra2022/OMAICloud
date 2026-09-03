"""
OM Universal Robotics Intelligence Manager
"""


from .world_model import WorldModel

from .perception import RobotPerception

from .reasoning import PhysicalReasoning

from .planning import RobotPlanner

from .adaptation import AdaptationEngine

from .skill_learning import SkillLearning

from .robot_memory import RobotMemory




class UniversalRoboticsManager:



    def __init__(self):

        self.world = WorldModel()

        self.perception = RobotPerception()

        self.reasoning = PhysicalReasoning()

        self.planner = RobotPlanner()

        self.adaptation = AdaptationEngine()

        self.skills = SkillLearning()

        self.memory = RobotMemory()



    def execute(

        self,

        goal,

        observation

    ):


        perception=self.perception.analyze(

            observation

        )


        world=self.world.update(

            perception

        )


        reasoning=self.reasoning.reason(

            world

        )


        plan=self.planner.create_plan(

            goal

        )


        result={


            "world":

                world,


            "reasoning":

                reasoning,


            "plan":

                plan

        }


        self.memory.store(

            result

        )


        return result