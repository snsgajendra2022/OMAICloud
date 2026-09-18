from .search_provider import SearchProvider



class SearchAgent:



    def __init__(
        self,
        provider:SearchProvider
    ):

        self.provider=provider



    def search(
        self,
        query
    ):


        return self.provider.search(
            query
        )