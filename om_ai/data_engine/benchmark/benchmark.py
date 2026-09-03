"""
OM Dataset Benchmark Engine
"""


from .evaluator import DatasetEvaluator





class DatasetBenchmark:



    def __init__(self):


        self.evaluator = DatasetEvaluator()




    def run(

        self,

        dataset:list[dict]

    ):


        results=[]


        approved=0



        for item in dataset:


            result=self.evaluator.evaluate(
                item
            )


            results.append(

                {

                    "item":

                        item,


                    "evaluation":

                        result

                }

            )


            if result["approved"]:

                approved +=1




        return {


            "total":

                len(dataset),


            "approved":

                approved,


            "rejected":

                len(dataset)-approved,


            "accuracy":

                round(

                    approved /
                    max(1,len(dataset)),

                    3

                ),


            "results":

                results

        }