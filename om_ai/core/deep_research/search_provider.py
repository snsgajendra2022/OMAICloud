from abc import ABC, abstractmethod



class SearchProvider(ABC):


    @abstractmethod
    def search(
        self,
        query:str
    ):
        pass