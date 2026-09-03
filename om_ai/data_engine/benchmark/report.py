"""
OM Benchmark Report Generator
"""





class BenchmarkReport:



    def generate(

        self,

        result:dict

    ):


        return {


            "dataset_size":

                result.get(
                    "total"
                ),


            "accepted":

                result.get(
                    "approved"
                ),


            "rejected":

                result.get(
                    "rejected"
                ),


            "quality_score":

                result.get(
                    "accuracy"
                )

        }