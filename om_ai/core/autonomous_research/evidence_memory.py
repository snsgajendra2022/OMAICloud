class EvidenceMemory:



    def __init__(self):

        self.items=[]



    def store(
        self,
        item
    ):

        self.items.append(
            item
        )



    def all(self):

        return self.items