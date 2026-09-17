from __future__ import annotations


class KnowledgeConfidence:


    def calculate(
        self,
        matches: int,
        quality: float = 1.0
    ) -> float:


        if matches <= 0:
            return 0.0


        score = (
            min(matches / 10, 1.0)
            *
            quality
        )


        return round(
            score,
            4
        )