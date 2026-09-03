"""
OM Training Quality Filter
"""



class QualityFilter:



    def __init__(
        self,
        minimum_score=0.7
    ):

        self.minimum_score = minimum_score




    def filter(
        self,
        items:list[dict]
    ):


        result=[]


        for item in items:


            score=float(

                item.get(
                    "quality_score",
                    0
                )

            )


            if score >= self.minimum_score:

                result.append(item)



        return result