"""
OM Long Term Learning Engine
"""


from .extractor import ExperienceExtractor

from .pattern_store import PatternStore





class LearningEngine:



    def __init__(self):


        self.extractor = ExperienceExtractor()

        self.store = PatternStore()




    def learn(

        self,

        question,

        answer,

        evaluation

    ):


        experience = self.extractor.extract(

            question,

            answer,

            evaluation

        )


        self.store.save(

            experience

        )


        return {


            "stored":

                True,


            "success":

                experience.success,


            "category":

                experience.category


        }