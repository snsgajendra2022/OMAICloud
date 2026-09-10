from __future__ import annotations


class ContradictionDetector:


    def detect(
        self,
        responses:list[str]
    ):


        result={

            "contradiction":

                False,

            "reason":

                None

        }


        if len(responses)<2:

            return result



        lengths=[

            len(x)

            for x in responses

        ]


        # basic conflict signal

        if max(lengths)-min(lengths)>2000:


            result["reason"]=(
                "large_answer_difference"
            )


        return result