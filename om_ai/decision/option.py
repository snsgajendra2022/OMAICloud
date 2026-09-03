"""
OM Decision Option Model
"""


from dataclasses import dataclass, field





@dataclass
class DecisionOption:


    name: str


    description: str


    benefits: list[str] = field(
        default_factory=list
    )


    risks: list[str] = field(
        default_factory=list
    )


    cost_score: float = 0.0


    performance_score: float = 0.0


    complexity_score: float = 0.0



    def to_dict(self):

        return {

            "name":
                self.name,

            "description":
                self.description,

            "benefits":
                self.benefits,

            "risks":
                self.risks,

            "cost":
                self.cost_score,

            "performance":
                self.performance_score,

            "complexity":
                self.complexity_score

        }