"""
OM Execution Plan

Defines agent execution flow.
"""


from dataclasses import dataclass, field





@dataclass
class ExecutionPlan:


    agent: str = "general"


    tools: list[str] = field(
        default_factory=list
    )


    knowledge_required: bool = True


    memory_required: bool = True


    steps: list[str] = field(
        default_factory=list
    )



    def to_dict(self):

        return {

            "agent":
                self.agent,

            "tools":
                self.tools,

            "knowledge_required":
                self.knowledge_required,

            "memory_required":
                self.memory_required,

            "steps":
                self.steps

        }