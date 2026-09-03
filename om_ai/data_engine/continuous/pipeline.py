"""
OM Continuous Learning Pipeline
"""


from .validator import DatasetValidator

from .deduplicator import DatasetDeduplicator

from .quality_filter import QualityFilter

from .version_manager import DatasetVersionManager





class ContinuousLearningPipeline:



    def __init__(self):


        self.validator=DatasetValidator()

        self.dedup=DatasetDeduplicator()

        self.quality=QualityFilter()

        self.version=DatasetVersionManager()




    def process(

        self,

        dataset:list[dict]

    ):


        valid=[]


        for item in dataset:


            result=self.validator.validate(
                item
            )


            if result["valid"]:

                valid.append(item)



        clean=self.dedup.remove(
            valid
        )


        filtered=self.quality.filter(
            clean
        )


        version_file=self.version.save(
            filtered
        )


        return {


            "input":

                len(dataset),


            "valid":

                len(valid),


            "final":

                len(filtered),


            "version":

                version_file

        }