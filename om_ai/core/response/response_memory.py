from __future__ import annotations


class ResponseMemory:


    def __init__(self):

        self.patterns={}



    def remember(
        self,
        intent,
        result
    ):


        key=intent


        if key not in self.patterns:

            self.patterns[key]=[]


        self.patterns[key].append(
            result
        )


    def get(
        self,
        intent
    ):

        return self.patterns.get(
            intent,
            []
        )