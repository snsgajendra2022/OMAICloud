class ContextRetriever:


    def search(
        self,
        messages,
        query
    ):


        results=[]


        query_words=set(
            query.lower().split()
        )


        for item in messages:


            words=set(
                item["content"]
                .lower()
                .split()
            )


            if query_words.intersection(words):

                results.append(
                    item
                )


        return results