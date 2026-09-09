class KnowledgeStore:


    def __init__(self):

        self.items=[]



    def add(
        self,
        item
    ):

        self.items.append(
            item
        )



    def search(
        self,
        query
    ):


        results=[]


        words=query.lower().split()


        for item in self.items:


            content = (
                item.content.lower()
            )


            for word in words:

                if word in content:

                    results.append(
                        item
                    )

                    break


        return results