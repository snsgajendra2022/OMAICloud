class KnowledgeBuilder:



    def build(
        self,
        patterns
    ):


        knowledge=[]


        for pattern in patterns:

            knowledge.append({

                "concept":pattern,

                "source":
                "experience_learning"

            })


        return knowledge