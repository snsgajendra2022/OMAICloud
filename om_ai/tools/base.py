"""
OM Tool Base Interface
"""


from abc import ABC, abstractmethod



class BaseTool(ABC):


    name="base"



    @abstractmethod
    def can_handle(
        self,
        request:str
    ) -> float:

        pass



    @abstractmethod
    def execute(
        self,
        request:str,
        context=None
    ):

        pass