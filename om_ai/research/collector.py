"""
OM Information Collection Engine
"""


class InformationCollector:


    def collect(

        self,

        question,

        knowledge=None

    ):


        sources=[]


        if knowledge:


            if isinstance(

                knowledge,

                list

            ):

                sources.extend(

                    knowledge

                )


            else:

                sources.append(

                    knowledge

                )


        return {


            "query":

                question,


            "sources":

                sources,


            "count":

                len(sources)

        }