from dataclasses import dataclass, field
from datetime import datetime



@dataclass
class BrainContext:


    user_input:str


    intent:str = ""


    domain:str = ""


    requires_research:bool=False


    memory={}


    knowledge={}


    reasoning={}


    agents=[]


    activities:list = field(
        default_factory=list
    )


    created_at:str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )