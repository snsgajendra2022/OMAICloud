from __future__ import annotations


from .dataset_quality import (
    DatasetQualityEvaluator
)

from .duplicate_detector import (
    DuplicateDetector
)

from .contamination_filter import (
    ContaminationFilter
)

from .dataset_validator import (
    DatasetValidator
)

from .dataset_memory import (
    DatasetMemory
)



class DatasetIntelligenceEngine:
    """
    OM Dataset Intelligence Brain.
    """


    def __init__(self):

        self.quality = (
            DatasetQualityEvaluator()
        )

        self.duplicate = (
            DuplicateDetector()
        )

        self.filter = (
            ContaminationFilter()
        )

        self.validator = (
            DatasetValidator()
        )

        self.memory = (
            DatasetMemory()
        )



    def process(
        self,
        item
    ):


        validation = (
            self.validator.validate(
                item
            )
        )


        if not validation["valid"]:

            return {

                "accepted": False,

                "reason":
                    validation["issues"]

            }



        contamination = (
            self.filter.check(
                item.output
            )
        )


        if not contamination["safe"]:

            return {

                "accepted": False,

                "reason":
                    "contamination"

            }



        if self.duplicate.is_duplicate(
            item
        ):

            return {

                "accepted": False,

                "reason":
                    "duplicate"

            }



        item.quality_score = (
            self.quality.evaluate(
                item
            )
        )


        self.memory.add(
            item
        )


        return {

            "accepted": True,

            "quality":
                item.quality_score

        }