class DatasetSelector:


    def select(
        self,
        capability
    ):


        return {

            "dataset":

                f"data/training/{capability}.jsonl",


            "type":

                "sft"

        }