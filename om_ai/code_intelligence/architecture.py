"""
OM Architecture Understanding Engine
"""




class ArchitectureAnalyzer:



    def analyze(

        self,

        files:list

    ):


        structure={


            "backend":[],

            "frontend":[],

            "database":[],

            "configuration":[]

        }



        for file in files:


            lower=file.lower()



            if any(

                x in lower

                for x in [

                    "controller",

                    "service",

                    "api"

                ]

            ):

                structure["backend"].append(file)



            elif any(

                x in lower

                for x in [

                    "component",

                    "page",

                    "view"

                ]

            ):

                structure["frontend"].append(file)



            elif any(

                x in lower

                for x in [

                    "migration",

                    "model",

                    "schema"

                ]

            ):

                structure["database"].append(file)



            elif any(

                x in lower

                for x in [

                    "config",

                    ".env"

                ]

            ):

                structure["configuration"].append(file)



        return structure