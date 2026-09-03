"""
OM Curriculum Builder
"""


class CurriculumBuilder:



    def build(

        self,

        examples:list[dict]

    ):


        curriculum={}



        for item in examples:


            domain=item.get(
                "domain",
                "general"
            )


            curriculum.setdefault(

                domain,

                []

            )


            curriculum[domain].append(

                {

                    "difficulty":

                    item.get(
                        "difficulty"
                    ),

                    "skills":

                    item.get(
                        "skills",
                        []
                    )

                }

            )



        return curriculum