from __future__ import annotations



class LearningMemory:
    """
    Stores historical improvement cycles.
    """



    def __init__(self):

        self.history = []



    def add(
        self,
        record
    ):

        self.history.append(
            record
        )



    def get_all(self):

        return self.history