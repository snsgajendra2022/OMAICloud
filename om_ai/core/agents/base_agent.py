from abc import ABC, abstractmethod


class BaseAgent(ABC):


    name = "base"


    @abstractmethod
    def execute(
        self,
        task,
        context=None
    ):

        pass