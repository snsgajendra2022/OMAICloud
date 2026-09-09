from dataclasses import dataclass, field


@dataclass
class AgentProfile:


    name: str


    role: str


    skills: list[str] = field(
        default_factory=list
    )


    experience: float = 0.0


    status: str = "idle"