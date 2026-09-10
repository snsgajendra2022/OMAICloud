from __future__ import annotations

from dataclasses import asdict
from typing import Any
import logging


from .knowledge_extractor import (
    KnowledgeExtractor,
)

from .knowledge_distiller import (
    KnowledgeDistiller,
)

from .knowledge_writer import (
    KnowledgeWriter,
)

from .dataset_builder import (
    DatasetBuilder,
)

from .sft_builder import (
    SFTBuilder,
)

from .preference_builder import (
    PreferenceBuilder,
)

from .evaluation_builder import (
    EvaluationBuilder,
)

from .provenance_manager import (
    ProvenanceManager,
)


logger = logging.getLogger(
    "om.distillation"
)



class DistillationEngine:
    """
    Main OM Knowledge Distillation Pipeline.

    This is the coordinator layer.

    It does not replace:

    - OM Native Model
    - OM Memory
    - OM Knowledge
    - OM Training

    It only prepares intelligence assets.
    """


    def __init__(
        self,
        teacher_manager=None,
        quality_evaluator=None,
        agreement_engine=None,
        contradiction_detector=None,
    ):


        self.teacher_manager = (
            teacher_manager
        )


        self.quality_evaluator = (
            quality_evaluator
        )


        self.agreement_engine = (
            agreement_engine
        )


        self.contradiction_detector = (
            contradiction_detector
        )


        self.knowledge_extractor = (
            KnowledgeExtractor()
        )


        self.knowledge_distiller = (
            KnowledgeDistiller()
        )


        self.knowledge_writer = (
            KnowledgeWriter()
        )


        self.dataset_builder = (
            DatasetBuilder()
        )


        self.sft_builder = (
            SFTBuilder(
                self.dataset_builder
            )
        )


        self.preference_builder = (
            PreferenceBuilder(
                self.dataset_builder
            )
        )


        self.evaluation_builder = (
            EvaluationBuilder(
                self.dataset_builder
            )
        )


        self.provenance = (
            ProvenanceManager()
        )



    def distill(
        self,
        question: str,
        domain: str = "general",
        evidence=None,
    ) -> dict[str, Any]:


        logger.info(
            "Starting distillation: %s",
            question
        )


        if not self.teacher_manager:

            raise RuntimeError(
                "Teacher manager not configured"
            )


        #
        # 1. Query teachers
        #

        teacher_results = (

            self.teacher_manager
            .ask_teachers(
                question
            )

        )



        responses = []


        for result in teacher_results:


            item = {


                "teacher":

                    getattr(
                        result,
                        "teacher",
                        "unknown"
                    ),


                "response":

                    getattr(
                        result,
                        "response",
                        str(result)
                    )

            }


            responses.append(
                item
            )



        #
        # 2. Quality filtering
        #

        approved = []


        evaluations = []



        for item in responses:


            evaluation = {


                "teacher":

                    item["teacher"],


                "score":

                    0.0,


                "approved":

                    True

            }



            if self.quality_evaluator:


                evaluation = (

                    self.quality_evaluator
                    .evaluate(

                        question,

                        item["response"]

                    )

                )



            evaluations.append(
                evaluation
            )



            if evaluation.get(
                "approved",
                True
            ):


                approved.append(
                    item
                )



        if not approved:

            return {


                "approved":

                    False,


                "reason":

                    "No teacher response passed quality evaluation",


                "evaluations":

                    evaluations

            }



        #
        # 3. Agreement analysis
        #

        agreement = {}


        if self.agreement_engine:


            agreement = (

                self.agreement_engine
                .analyze(
                    approved
                )

            )



        #
        # 4. Contradiction detection
        #

        contradictions = []


        if self.contradiction_detector:


            contradictions = (

                self.contradiction_detector
                .detect(
                    approved
                )

            )



        #
        # 5. Knowledge extraction
        #

        extracted = (

            self.knowledge_extractor
            .extract(

                topic=question,

                responses=approved

            )

        )



        #
        # 6. Knowledge distillation
        #

        distilled = (

            self.knowledge_distiller
            .distill(

                [
                    extracted
                ]

            )

        )



        #
        # 7. Save OM knowledge
        #

        knowledge_file = (

            self.knowledge_writer
            .save(
                distilled
            )

        )



        #
        # 8. Create SFT data
        #

        best_answer = (

            approved[0]
            ["response"]

        )


        sft_file = (

            self.sft_builder
            .create_example(

                question,

                best_answer,

                {

                    "domain":
                        domain,

                    "teachers":
                        [

                            x["teacher"]

                            for x in approved

                        ]

                }

            )

        )



        #
        # 9. Evaluation data
        #

        eval_file = (

            self.evaluation_builder
            .add_example(

                question,

                best_answer,

                {

                    "domain":
                        domain

                }

            )

        )



        #
        # 10. Provenance
        #

        provenance = (

            self.provenance
            .create(

                question,

                [

                    x["teacher"]

                    for x in approved

                ],

                {

                    "domain":
                        domain,

                    "knowledge_file":
                        knowledge_file

                }

            )

        )



        return {


            "approved":

                True,


            "question":

                question,


            "domain":

                domain,


            "teachers":

                approved,


            "evaluations":

                evaluations,


            "agreement":

                agreement,


            "contradictions":

                contradictions,


            "knowledge":

                asdict(
                    distilled
                ),


            "knowledge_file":

                knowledge_file,


            "sft":

                sft_file,


            "evaluation":

                eval_file,


            "provenance":

                provenance

        }



    def distill_dataset(
        self,
        questions: list[str],
        domain="general",
    ):


        results=[]


        for question in questions:


            try:

                results.append(

                    self.distill(

                        question,

                        domain

                    )

                )


            except Exception as error:


                logger.exception(
                    error
                )


                results.append({

                    "approved":
                        False,

                    "error":
                        str(error)

                })


        return results