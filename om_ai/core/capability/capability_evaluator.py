from __future__ import annotations



class CapabilityEvaluator:
    """
    Evaluates OM performance.

    Input:

    task result
    quality score
    feedback

    """


    def evaluate(
        self,
        quality: float,
        success: bool
    ):


        score = quality


        if not success:

            score *= 0.7



        return max(
            0.0,
            min(
                score,
                1.0
            )
        )