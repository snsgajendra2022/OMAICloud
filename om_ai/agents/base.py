"""
OM Agent Base Class
"""


from __future__ import annotations


from abc import ABC, abstractmethod




class BaseAgent(ABC):


    name = "base"



    @abstractmethod
    def can_handle(
        self,
        question:str
    ) -> float:
        pass



    @abstractmethod
    def execute(
        self,
        question:str,
        context=None
    ):

        pass