"""
OM Knowledge Confidence Engine

Checks:

- Retrieval quality
- Source quality
- Context availability
- Answer confidence
"""


from __future__ import annotations


from dataclasses import dataclass

from typing import Any



@dataclass
class KnowledgeConfidence:


    score: float

    confidence: str

    reasons: list[str]

    retry_needed: bool




class KnowledgeConfidenceEngine:



    def evaluate(
        self,
        question: str,
        knowledge: list[dict[str, Any]] | None
    ) -> KnowledgeConfidence:


        reasons = []


        if not knowledge:

            return KnowledgeConfidence(

                score=0.0,

                confidence="low",

                reasons=[
                    "no knowledge retrieved"
                ],

                retry_needed=True

            )



        scores = []


        for item in knowledge:


            score = float(

                item.get(
                    "hybrid_score",

                    item.get(
                        "score",
                        0
                    )

                )

                or 0

            )


            scores.append(score)



        best = max(
            scores
        )



        if best >= 0.80:


            level = "high"


            reasons.append(
                "strong knowledge match"
            )


        elif best >= 0.50:


            level="medium"


            reasons.append(
                "partial knowledge match"
            )


        else:


            level="low"


            reasons.append(
                "weak knowledge match"
            )



        retry = best < 0.40



        return KnowledgeConfidence(

            score=round(
                best,
                3
            ),

            confidence=level,

            reasons=reasons,

            retry_needed=retry

        )