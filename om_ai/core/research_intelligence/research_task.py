from dataclasses import dataclass



@dataclass
class ResearchTask:

    query:str

    reason:str

    priority:float = 0.5