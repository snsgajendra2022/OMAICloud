"""
OM Data Engine
Quality Scoring
"""

from __future__ import annotations

import re



class QualityScorer:


    def score(
        self,
        text: str
    ) -> float:


        if not text:

            return 0.0



        length_score = min(
            len(text) / 1000,
            1
        )



        words = re.findall(
            r"\w+",
            text.lower()
        )


        unique_score = (

            len(set(words))
            /
            max(len(words),1)

        )



        readable = sum(

            c.isprintable()

            for c in text

        ) / len(text)



        final = (

            length_score * 0.3

            +

            unique_score * 0.4

            +

            readable * 0.3

        )


        return round(
            min(final,1),
            3
        )



    def accepted(
        self,
        text: str,
        threshold: float = 0.50
    ) -> bool:


        return self.score(text) >= threshold