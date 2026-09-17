from __future__ import annotations



class DatasetMemory:


    def __init__(self):

        self.items=[]



    def add(
        self,
        item
    ):

        self.items.append(
            item
        )



    def all(self):

        return self.items