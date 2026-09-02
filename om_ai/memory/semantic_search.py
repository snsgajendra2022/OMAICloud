"""
Semantic Memory Retrieval

Finds relevant memories.
"""


import re



class SemanticMemorySearch:



    def tokens(
        self,
        text
    ):


        return set(

            re.findall(

                r"[a-zA-Z0-9]+",

                text.lower()

            )

        )



    def search(
        self,
        query,
        memories,
        limit=5
    ):


        q=self.tokens(query)


        scored=[]


        for memory in memories:


            text=str(memory)


            m=self.tokens(text)


            if not m:

                continue



            score=len(

                q.intersection(m)

            ) / len(q)



            scored.append(

                {
                    "memory":text,
                    "score":round(score,3)
                }

            )



        scored.sort(

            key=lambda x:x["score"],

            reverse=True

        )


        return scored[:limit]