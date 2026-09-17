class ContextWindow:


    def __init__(
        self,
        size:int=20
    ):

        self.size=size



    def compress(
        self,
        messages:list
    ):


        if len(messages)<=self.size:

            return messages



        return messages[-self.size:]