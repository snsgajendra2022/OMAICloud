from dataclasses import dataclass



@dataclass
class AgentIdentity:


    agent_id:str

    name:str

    version:str="1.0"