from dataclasses import dataclass, field


@dataclass
class Mission:


    goal: str


    tasks: list[str] = field(
        default_factory=list
    )


    status: str = "created"


    assigned_agents:list[str] = field(
        default_factory=list
    )