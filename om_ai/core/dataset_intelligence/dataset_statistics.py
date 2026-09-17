from __future__ import annotations



class DatasetStatistics:


    def calculate(
        self,
        items
    ):


        return {

            "total":

                len(items),


            "sft":

                len(

                    [

                    x for x in items

                    if x.dataset_type=="sft"

                    ]

                ),


            "average_quality":

                (

                    sum(

                        x.quality_score

                        for x in items

                    )

                    /

                    max(
                        len(items),
                        1
                    )

                )

        }