class ResearchScheduler:



    def __init__(self):

        self.queue=[]



    def add(
        self,
        goal
    ):

        self.queue.append(
            goal
        )



    def next(self):

        if self.queue:

            return self.queue.pop(0)

        return None