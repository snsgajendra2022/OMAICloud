"""
Extract project related memories.
"""


import re



class ProjectMemoryExtractor:



    def extract(
        self,
        text:str
    ):


        results=[]


        patterns=[


            r"my project (.+)",


            r"project name is (.+)",


            r"(.+) project uses (.+)",


            r"we are building (.+)"


        ]



        for pattern in patterns:


            match=re.search(
                pattern,
                text,
                re.I
            )


            if match:


                results.append(

                    match.group(0)

                )


        return results