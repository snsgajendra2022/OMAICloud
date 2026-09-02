"""
OM Vector Retriever

Connects:

Question
   ↓
Embedding
   ↓
Vector Store
   ↓
Relevant Knowledge
"""


from __future__ import annotations


from typing import Any


from om_ai.knowledge.storage.vector_store import VectorStore

from om_ai.knowledge.processing.embedder import EmbeddingEngine



class VectorRetriever:


    def __init__(self):

        self.embedder = EmbeddingEngine()

        self.store = VectorStore()



    def search(
        self,
        query: str,
        k: int = 5,
        metadata_filter: dict[str, Any] | None = None
    ):


        vector = self.embedder.encode(
            query
        )


        results = self.store.search(
            vector,
            limit=k
        )


        filtered = []


        for item in results:


            metadata = item.get(
                "metadata",
                {}
            )


            if metadata_filter:


                matched = True


                for key,value in metadata_filter.items():

                    if metadata.get(key) != value:

                        matched=False


                if not matched:

                    continue



            filtered.append(item)


        return filtered