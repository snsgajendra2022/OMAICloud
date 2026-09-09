from dataclasses import dataclass, field

@dataclass

class LearningState:

    experiences: list = field(
        default_factory=list
    )


    improvements: list = field(
        default_factory=list
    )

    confidence: float = 0.0

    def __init__(self):

        self.total_experiences = 0

        self.improvements = 0



    def add_experience(self):

        self.total_experiences += 1



    def add_improvement(self):

        self.improvements += 1



