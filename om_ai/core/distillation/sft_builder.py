from __future__ import annotations


class SFTBuilder:
    """
    Creates supervised fine tuning examples.

    Format:

    instruction
    input
    output
    metadata
    """


    def __init__(
        self,
        dataset_builder
    ):

        self.builder = dataset_builder



    def create_example(
        self,
        question: str,
        answer: str,
        metadata=None
    ):


        data = {

            "instruction":
                question,

            "input":
                "",

            "output":
                answer,

            "metadata":
                metadata or {}

        }


        return self.builder.append_jsonl(
            "sft.jsonl",
            data
        )