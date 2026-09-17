from __future__ import annotations



class KnowledgeIngestion:


    def __init__(
        self,
        memory
    ):

        self.memory = memory



    def ingest(
        self,
        knowledge:dict
    ):


        topic = knowledge.get(
            "topic"
        )


        if not topic:

            return False



        self.memory.store(
            topic,
            knowledge
        )


        return True