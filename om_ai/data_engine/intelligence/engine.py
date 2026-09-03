"""
OM Training Data Intelligence Engine
"""


from .domain_classifier import DomainClassifier

from .difficulty import DifficultyDetector

from .skill_mapper import SkillMapper

from .curriculum import CurriculumBuilder





class TrainingDataIntelligence:



    def __init__(self):


        self.domain=DomainClassifier()

        self.difficulty=DifficultyDetector()

        self.skills=SkillMapper()

        self.curriculum=CurriculumBuilder()




    def analyze(

        self,

        dataset:list[dict]

    ):


        enriched=[]



        for item in dataset:


            text=(

                item.get("instruction","")

                +

                " "

                +

                item.get("response","")

            )



            item["domain"]=self.domain.classify(
                text
            )


            item["difficulty"]=self.difficulty.detect(
                text
            )


            item["skills"]=self.skills.map(
                text
            )


            enriched.append(item)



        return {


            "dataset":

                enriched,


            "curriculum":

                self.curriculum.build(
                    enriched
                )

        }