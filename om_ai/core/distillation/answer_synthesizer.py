from __future__ import annotations



class AnswerSynthesizer:


    def synthesize(
        self,
        responses:list[str],
        evaluations:list[dict]
    ):


        if not responses:

            return ""


        scored=[]


        for response, evaluation in zip(
            responses,
            evaluations
        ):

            scored.append(

                (
                    evaluation.get(
                        "score",
                        0
                    ),

                    response

                )

            )


        scored.sort(
            reverse=True
        )


        return scored[0][1]