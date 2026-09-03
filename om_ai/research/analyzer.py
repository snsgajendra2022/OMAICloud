"""
OM Research Analysis Engine
"""


class ResearchAnalyzer:


    def analyze(

        self,

        data:dict

    ):


        sources=data.get(

            "sources",

            []

        )


        return {


            "key_points":

                [

                    str(item)

                    for item in sources[:10]

                ],


            "source_count":

                len(sources)

        }