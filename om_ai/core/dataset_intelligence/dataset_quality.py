from __future__ import annotations



class DatasetQualityEvaluator:
    """
    Evaluates training example quality.
    """


    def evaluate(
        self,
        item
    ):


        score = 0


        if item.instruction.strip():

            score += 0.3


        if item.output.strip():

            score += 0.3


        if len(item.output) > 50:

            score += 0.2


        if len(item.instruction) > 10:

            score += 0.2


        return min(
            score,
            1.0
        )