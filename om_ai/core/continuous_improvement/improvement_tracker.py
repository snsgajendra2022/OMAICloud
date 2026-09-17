from __future__ import annotations



class ImprovementTracker:


    def __init__(self):

        self.events=[]



    def add(
        self,
        event
    ):

        self.events.append(
            event
        )



    def all(self):

        return self.events