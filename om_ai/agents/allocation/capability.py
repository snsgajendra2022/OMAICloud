"""
OM Agent Capability Model
"""


from dataclasses import dataclass, field



@dataclass
class AgentCapability:


    name: str


    skills: list[str] = field(
        default_factory=list
    )


    domains: list[str] = field(
        default_factory=list
    )


    priority: float = 1.0



    def matches(self, task:str):

        text = task.lower()

        score = 0


        for skill in self.skills:

            if skill.lower() in text:

                score += 0.2



        for domain in self.domains:

            if domain.lower() in text:

                score += 0.3



        return min(score * self.priority, 1.0)