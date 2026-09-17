from dataclasses import dataclass, field



@dataclass
class ReasoningState:


    problem:str


    steps:list[str]=field(
        default_factory=list
    )


    assumptions:list[str]=field(
        default_factory=list
    )


    confidence:float=0.0