"""
Extract useful memories from conversations.
"""


import re



class MemoryExtractor:



    def extract(
        self,
        text:str
    ):


        memories=[]


        patterns=[

            r"my project is (.+)",

            r"my name is (.+)",

            r"I use (.+)",

            r"remember (.+)"

        ]


        for pattern in patterns:


            match=re.search(
                pattern,
                text,
                re.I
            )


            if match:

                memories.append(
                    match.group(1)
                )


        return memories