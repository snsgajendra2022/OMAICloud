"""
OM Experience Knowledge Extractor
"""





class ExperienceExtractor:



    def extract(

        self,

        experience:dict

    ):


        content=experience.get(

            "content",

            {}

        )


        knowledge={}



        if "technology" in content:


            knowledge["technology"] = content["technology"]



        if "decision" in content:


            knowledge["decision"] = content["decision"]



        if "project" in content:


            knowledge["project"] = content["project"]



        return knowledge