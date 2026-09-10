from __future__ import annotations


import uuid


class HarvestEngine:
    """
    Autonomous OM knowledge harvesting controller.

    It coordinates:

    Question source
        |
        ↓
    Teacher system
        |
        ↓
    Dataset creation
        |
        ↓
    Checkpoint

    """


    def __init__(
        self,
        teacher_manager,
        progress_tracker,
        checkpoint_manager,
        provenance_manager
    ):


        self.teacher_manager = teacher_manager

        self.progress_tracker = progress_tracker

        self.checkpoint_manager = checkpoint_manager

        self.provenance_manager = provenance_manager



    def harvest_question(
        self,
        question
    ):


        run_id = str(
            uuid.uuid4()
        )


        try:


            responses = (

                self.teacher_manager
                .ask_teachers(
                    question
                )

            )


            provenance = (

                self.provenance_manager
                .create(

                    question,

                    [

                        r.teacher

                        for r in responses

                    ]

                )

            )



            self.progress_tracker.mark_completed(

                provenance["provenance_id"]

            )


            self.checkpoint_manager.save(

                run_id,

                {

                    "question":

                        question,

                    "responses":

                        len(responses),

                    "provenance":

                        provenance

                }

            )


            return {


                "run_id":

                    run_id,


                "question":

                    question,


                "responses":

                    responses,


                "provenance":

                    provenance


            }


        except Exception as error:


            self.progress_tracker.mark_failed(

                run_id,

                error

            )


            raise