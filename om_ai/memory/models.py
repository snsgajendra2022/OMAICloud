"""
OM Memory Data Models
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryItem:


    id:int|None

    content:str

    memory_type:str


    project:str|None = None

    tags:list[str]|None = None


    importance:float = 0.5


    created_at:str=""


    def __post_init__(self):

        if not self.created_at:

            self.created_at = datetime.utcnow().isoformat()


        if self.tags is None:

            self.tags=[]