class MemoryRetriever:



    def retrieve(
        self,
        query,
        store
    ):


        words = query.lower().split()


        results=[]


        for word in words:

            results.extend(
                store.search(word)
            )


        return results