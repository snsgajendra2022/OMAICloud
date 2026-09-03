"""
OM Autonomous Memory Consolidation Engine
"""


from .importance import ImportanceAnalyzer

from .extractor import ExperienceExtractor

from .storage import ExperienceStorage





class MemoryConsolidator:



    def __init__(self):


        self.importance = ImportanceAnalyzer()

        self.extractor = ExperienceExtractor()

        self.storage = ExperienceStorage()




    def consolidate(

        self,

        experience:dict

    ):


        score=self.importance.score(

            experience

        )


        experience["importance"]=score



        if score >= 0.3:


            extracted=self.extractor.extract(

                experience

            )


            record={


                "experience":

                    experience,


                "knowledge":

                    extracted

            }



            self.storage.add(

                record

            )



            return {


                "stored":

                    True,


                "importance":

                    score,


                "knowledge":

                    extracted

            }



        return {


            "stored":

                False,


            "importance":

                score

        }