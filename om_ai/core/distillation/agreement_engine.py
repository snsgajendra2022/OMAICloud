from __future__ import annotations


class AgreementEngine:


    def compare(
        self,
        responses:list[str]
    ):


        if not responses:

            return {

                "consensus":0,

                "common":[]

            }



        normalized=[

            set(
                r.lower()
                .split()
            )

            for r in responses

        ]


        common=set.intersection(
            *normalized
        )


        total=len(normalized)


        return {


            "consensus":

                round(
                    len(common)
                    /
                    max(
                        len(
                            set.union(
                                *normalized
                            )
                        ),
                        1
                    ),

                    2
                ),


            "common_terms":

                list(common)[:50],


            "teacher_count":

                total

        }