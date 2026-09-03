"""
OM Research Summary Generator
"""


class ResearchSummarizer:


    def summarize(

        self,

        analysis,

        validation

    ):


        return {


            "summary":

                "\n".join(

                    analysis.get(

                        "key_points",

                        []

                    )

                ),


            "confidence":

                validation.get(

                    "confidence",

                    0

                )

        }