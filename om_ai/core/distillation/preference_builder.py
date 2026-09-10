from __future__ import annotations



class PreferenceBuilder:
    """
    Creates DPO preference pairs.

    chosen = better response

    rejected = weaker response
    """


    def __init__(
        self,
        dataset_builder
    ):

        self.builder = dataset_builder



    def create_pair(
        self,
        prompt: str,
        chosen: str,
        rejected: str,
        chosen_score: float,
        rejected_score: float,
        metadata=None
    ):


        if chosen == rejected:

            return None



        if chosen_score <= rejected_score:

            return None



        data = {


            "prompt":
                prompt,


            "chosen":
                chosen,


            "rejected":
                rejected,


            "metadata":{

                "chosen_score":
                    chosen_score,

                "rejected_score":
                    rejected_score,

                **(
                    metadata
                    or {}
                )

            }

        }


        return self.builder.append_jsonl(
            "dpo.jsonl",
            data
        )