from dataclasses import dataclass, field



@dataclass
class ResearchPlan:


    query:str


    depth:str="normal"


    sources_required:int=5


    research_needed:bool=True


    steps:list[str]=field(
        default_factory=list
    )