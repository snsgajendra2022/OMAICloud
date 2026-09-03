"""
OM Dataset Quality Metrics
"""


class DatasetMetrics:



    def completeness(
        self,
        item:dict
    ) -> float:


        score = 0


        if item.get(
            "instruction"
        ):

            score +=0.5


        if item.get(
            "response"
        ):

            score +=0.5


        return score




    def length_quality(
        self,
        item:dict
    ) -> float:


        response = item.get(
            "response",
            ""
        )


        length = len(
            response.split()
        )


        if length >= 20:

            return 1.0


        if length >= 5:

            return 0.6


        return 0.2




    def diversity(
        self,
        item:dict
    ) -> float:


        if item.get(
            "category"
        ):

            return 1.0


        return 0.5