class ResearchMemory:


    def __init__(self):

        self.records=[]



    def add(
        self,
        item
    ):

        self.records.append(
            item
        )



    def all(self):

        return self.records