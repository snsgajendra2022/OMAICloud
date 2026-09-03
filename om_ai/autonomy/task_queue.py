"""
OM Task Queue

Stores execution tasks.
"""




class TaskQueue:



    def __init__(self):

        self.tasks=[]



    def add(
        self,
        task:str
    ):

        self.tasks.append(task)



    def next(self):

        if not self.tasks:

            return None


        return self.tasks.pop(0)



    def size(self):

        return len(self.tasks)