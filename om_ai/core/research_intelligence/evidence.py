from dataclasses import dataclass



@dataclass
class Evidence:

    content:str

    source:str

    confidence:float