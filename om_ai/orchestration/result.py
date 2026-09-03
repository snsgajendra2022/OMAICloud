"""
OM Orchestration Result
"""



from dataclasses import dataclass, field





@dataclass
class OrchestrationResult:


    answer: str = ""


    agent: str = ""


    tools_used: list[str] = field(
        default_factory=list
    )


    knowledge_used: int = 0


    metadata: dict = field(
        default_factory=dict
    )



    def to_dict(self):

        return {


            "answer":

                self.answer,


            "agent":

                self.agent,


            "tools_used":

                self.tools_used,


            "knowledge_used":

                self.knowledge_used,


            "metadata":

                self.metadata

        }