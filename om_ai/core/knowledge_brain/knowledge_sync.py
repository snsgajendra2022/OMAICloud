from __future__ import annotations



class KnowledgeSync:


    def sync(
        self,
        source,
        target
    ):


        data = source.all()


        for key,value in data.items():

            target.store(
                key,
                value
            )


        return len(data)