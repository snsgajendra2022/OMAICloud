from .requirement_analyzer import RequirementAnalyzer
from .architecture_planner import ArchitecturePlanner


class CodingIntelligence:


    def __init__(self):

        self.requirement = RequirementAnalyzer()

        self.architecture = ArchitecturePlanner()



    def analyze(
        self,
        message
    ):


        req = (
            self.requirement.analyze(
                message
            )
        )


        architecture = (
            self.architecture.create(
                req
            )
        )


        return {

            "requirement":req,

            "architecture":
                architecture

        }