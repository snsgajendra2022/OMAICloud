from __future__ import annotations



class DatasetValidator:


    def validate(
        self,
        item
    ):


        problems=[]


        if not item.instruction:

            problems.append(
                "missing_instruction"
            )


        if not item.output:

            problems.append(
                "missing_output"
            )


        return {

            "valid":
                len(problems)==0,

            "issues":
                problems

        }