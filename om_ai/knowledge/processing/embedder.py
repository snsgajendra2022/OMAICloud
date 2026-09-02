"""
OM Embedding Engine Interface

Later connect:
- sentence transformers
- local embedding models
- custom OM embeddings
"""


from typing import List



class EmbeddingEngine:


    def encode(
        self,
        text: str
    ) -> List[float]:

        """
        Placeholder embedding.

        Replace with real model.
        """

        values = [

            float(ord(c)%100)/100

            for c in text[:64]

        ]


        while len(values)<64:

            values.append(0.0)


        return values[:64]