"""
OM Keyword Search Engine

Exact keyword matching layer.
"""


from __future__ import annotations

import re



class KeywordSearch:


    def tokenize(
        self,
        text: str
    ) -> set[str]:

        return set(
            re.findall(
                r"[a-zA-Z0-9]{2,}",
                text.lower()
            )
        )



    def score(
        self,
        query: str,
        text: str
    ) -> float:

        query_tokens = self.tokenize(query)

        text_tokens = self.tokenize(text)


        if not query_tokens:

            return 0.0


        return round(
            len(query_tokens.intersection(text_tokens))
            /
            len(query_tokens),
            4
        )



    def search(
        self,
        query: str,
        documents: list[dict],
        k: int = 5
    ):

        results = []


        for doc in documents:

            text = str(
                doc.get("text", "")
            )


            score = self.score(
                query,
                text
            )


            if score > 0:

                results.append(
                    {
                        **doc,
                        "keyword_score": score
                    }
                )


        results.sort(
            key=lambda x: x["keyword_score"],
            reverse=True
        )


        return results[:k]