from __future__ import annotations



class EvaluationBuilder:
    """
    Creates evaluation-only datasets.

    These examples must not enter training.
    """


    def __init__(
        self,
        dataset_builder
    ):

        self.builder = dataset_builder



    def add_example(
        self,
        question: str,
        expected_answer: str,
        metadata=None
    ):


        data = {


            "question":
                question,


            "expected_answer":
                expected_answer,


            "metadata":
                metadata or {}

        }


        return self.builder.append_jsonl(
            "evaluation.jsonl",
            data
        )