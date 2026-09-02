import re


class MemoryImportance:


    def score(
        self,
        text:str
    ):

        score=0


        patterns=[

            "project",

            "remember",

            "always",

            "prefer",

            "architecture",

            "decision",

            "build",

            "use"

        ]


        for p in patterns:

            if p in text.lower():

                score +=0.15



        if len(text)>200:

            score+=0.2



        return min(
            score,
            1.0
        )



    def should_store(
        self,
        text
    ):

        return self.score(text)>=0.5