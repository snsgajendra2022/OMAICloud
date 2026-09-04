class ShortTermMemory:


    def __init__(self):

        self.context=[]



    def add(
        self,
        message
    ):

        self.context.append(
            message
        )



    def get(self):

        return self.context