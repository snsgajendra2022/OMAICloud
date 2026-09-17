from __future__ import annotations



class PreferenceRanker:
    """
    Creates preference decisions.

    Used for DPO generation.
    """


    def compare(
        self,
        answer_a,
        answer_b
    ):


        score_a = len(
            answer_a
        )


        score_b = len(
            answer_b
        )


        if score_a == score_b:

            return None



        if score_a > score_b:


            return {

                "chosen":
                    answer_a,

                "rejected":
                    answer_b

            }


        return {

            "chosen":
                answer_b,

            "rejected":
                answer_a

        }