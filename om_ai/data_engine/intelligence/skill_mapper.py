"""
OM Skill Mapping Engine
"""


class SkillMapper:



    def map(

        self,

        text:str

    ) -> list[str]:


        skills=[]


        mapping={


            "python":

                "python programming",


            "api":

                "api development",


            "database":

                "database design",


            "sql":

                "sql",


            "react":

                "frontend development",


            "docker":

                "deployment",


            "machine learning":

                "ml engineering"


        }



        value=text.lower()



        for key,skill in mapping.items():


            if key in value:

                skills.append(skill)



        return skills