"""
OM Hybrid Retriever

Combines:

1. Vector similarity
2. Keyword matching
3. Metadata filtering
"""


from __future__ import annotations


from om_ai.knowledge.vector_layer import VectorKnowledgeLayer

from om_ai.knowledge.retrieval.keyword_search import KeywordSearch




class HybridRetriever:


    def __init__(
        self
    ):

        self.vector = VectorKnowledgeLayer()

        self.keyword = KeywordSearch()



    def search(
        self,
        query: str,
        *,
        k: int = 5,
        filters=None
    ):


        vector_results = self.vector.search(

            query,

            k=k * 3,

            filters=filters

        )


        keyword_results = self.keyword.search(

            query,

            vector_results,

            k=k * 3

        )


        merged = {}



        for item in vector_results:

            key = item["text"][:120]

            merged[key] = item



        for item in keyword_results:


            key = item["text"][:120]


            if key in merged:

                vector_score = float(
                    merged[key].get(
                        "score",
                        0
                    )
                )


                keyword_score = float(
                    item.get(
                        "keyword_score",
                        0
                    )
                )


                merged[key]["hybrid_score"] = (

                    vector_score * 0.7

                    +

                    keyword_score * 0.3

                )


            else:

                item["hybrid_score"] = item.get(
                    "keyword_score",
                    0
                )

                merged[key] = item



        results = list(
            merged.values()
        )


        results.sort(

            key=lambda x:
            x.get(
                "hybrid_score",
                x.get("score",0)
            ),

            reverse=True

        )


        return results[:k]