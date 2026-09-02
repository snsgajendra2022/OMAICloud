"""
OM Knowledge Index

Manages searchable knowledge references.
"""


from dataclasses import dataclass


@dataclass
class KnowledgeChunk:

    id:str

    text:str

    source:str

    score:float=0.0



class KnowledgeIndex:


    def __init__(self):

        self.chunks=[]



    def add(
        self,
        chunk:KnowledgeChunk
    ):

        self.chunks.append(
            chunk
        )



    def search(
        self,
        keyword:str,
        limit:int=5
    ):

        results=[]


        for item in self.chunks:

            if keyword.lower() in item.text.lower():

                results.append(item)


        return results[:limit]