from __future__ import annotations



class EvaluationMemory:


    def __init__(self):

        self.records=[]



    def store(
        self,
        result
    ):

        self.records.append(
            result
        )



    def history(self):

        return self.records