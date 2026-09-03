"""
OM Autonomous Test Generator
"""


class TestGenerator:



    def generate(

        self,

        requirement:str

    ):


        tests=[]



        text=requirement.lower()



        if "login" in text:


            tests.extend([

                {

                    "name":
                    "Valid login test",

                    "category":
                    "authentication"

                },

                {

                    "name":
                    "Invalid password test",

                    "category":
                    "security"

                }

            ])




        if "api" in text:


            tests.append(

                {

                    "name":
                    "API response validation",

                    "category":
                    "integration"

                }

            )



        if "database" in text:


            tests.append(

                {

                    "name":
                    "Database operation test",

                    "category":
                    "database"

                }

            )



        if not tests:


            tests.append(

                {

                    "name":
                    "General functionality test",

                    "category":
                    "functional"

                }

            )


        return tests