"""
OM Situation Understanding
"""




class SituationAnalyzer:



    def analyze(

        self,

        context:dict

    ):


        task=context.get(

            "task",

            ""

        ).lower()



        situation={


            "type":

                "general",


            "priority":

                "normal",


            "domain":

                None

        }



        if any(

            word in task

            for word in [

                "error",

                "bug",

                "fix",

                "issue"

            ]

        ):


            situation["type"]="problem_solving"

            situation["priority"]="high"




        if any(

            word in task

            for word in [

                "build",

                "create",

                "develop"

            ]

        ):


            situation["type"]="development"



        technologies=[

            "laravel",

            "react",

            "python",

            "wordpress",

            "ionic"

        ]


        for tech in technologies:


            if tech in task:


                situation["domain"]=tech



        return situation