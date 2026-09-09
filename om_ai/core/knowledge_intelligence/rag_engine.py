class RAGEngine:



    def __init__(
        self,
        store
    ):

        self.store=store



    def retrieve(
        self,
        query
    ):


        documents = (
            self.store.search(
                query
            )
        )


        return {

            "query":query,

            "documents":
                documents

        }