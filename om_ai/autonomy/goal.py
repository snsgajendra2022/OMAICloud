"""
OM Goal Model

Represents user objectives.
"""


from dataclasses import dataclass, field





@dataclass
class Goal:


    description: str


    category: str = "general"


    completed: bool = False


    tasks: list[str] = field(
        default_factory=list
    )


    metadata: dict = field(
        default_factory=dict
    )