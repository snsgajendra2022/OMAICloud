class ReasoningMemory:


    def __init__(self):

        self.records=[]



    def store(
        self,
        item
    ):

        self.records.append(
            item
        )



    def history(self):

        return self.records