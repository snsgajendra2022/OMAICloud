"""
OM User Intelligence Extractor
"""





class UserExtractor:



    def extract(

        self,

        text:str

    ):


        text=text.lower()


        result={


            "technologies":[],

            "projects":[],

            "preferences":[]

        }



        technologies=[

            "python",

            "laravel",

            "react",

            "wordpress",

            "bagisto",

            "flutter",

            "ionic",

            "azure"

        ]



        for item in technologies:


            if item in text:

                result["technologies"].append(

                    item

                )



        project_words=[

            "project",

            "system",

            "application",

            "platform"

        ]



        for word in project_words:


            if word in text:

                result["projects"].append(

                    word

                )



        return result