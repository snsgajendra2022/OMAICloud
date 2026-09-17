from __future__ import annotations



class ComplexityMemory:
    """
    Stores historical difficulty analysis.
    """


    def __init__(self):

        self.records = []



    def add(
        self,
        item
    ):

        self.records.append(
            item
        )



    def history(self):

        return self.records