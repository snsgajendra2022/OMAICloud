"""
OM Quality Evaluation
"""



class QualityScore:



    def calculate(

        self,

        tests,

        analysis

    ):


        passed=len(

            [

                t

                for t in tests

                if t["status"]

                =="passed"

            ]

        )


        total=max(

            len(tests),

            1

        )


        test_score=passed/total



        code_score=analysis.get(

            "quality",

            0

        )



        return round(

            (

                test_score*0.6

                +

                code_score*0.4

            ),

            2

        )