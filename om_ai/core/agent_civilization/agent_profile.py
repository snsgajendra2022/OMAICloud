from dataclasses import dataclass, field



@dataclass
class AgentProfile:


    identity:any


    role:any


    skills:list[str]=field(
        default_factory=list
    )


    score:float=0.0