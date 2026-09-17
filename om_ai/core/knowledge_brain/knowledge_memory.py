from __future__ import annotations


class KnowledgeMemory:


    def __init__(self):

        self._memory = {}



    def store(
        self,
        key: str,
        value
    ):

        self._memory[key] = value



    def retrieve(
        self,
        key: str
    ):

        return self._memory.get(
            key
        )



    def search(
        self,
        text: str
    ):


        result = []


        text = text.lower()


        for key,value in self._memory.items():

            if key.lower() in text:

                result.append(value)


        return result



    def all(self):

        return self._memory