from dataclasses import dataclass



@dataclass
class Checkpoint:


    version:str


    path:str


    score:float


    status:str="created"