"""
OM Dependency Intelligence
"""




class DependencyAnalyzer:



    def analyze(

        self,

        content:str

    ):


        dependencies=[]



        patterns=[

            "import ",

            "from ",

            "require(",

            "use "

        ]



        for line in content.splitlines():

            line=line.strip()


            for pattern in patterns:


                if line.startswith(pattern):


                    dependencies.append(

                        line

                    )


        return dependencies