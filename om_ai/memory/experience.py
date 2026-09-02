"""
OM Experience Memory

Stores successful reasoning patterns.
"""


from dataclasses import dataclass



@dataclass
class Experience:

    question:str

    solution:str

    score:float=0.0