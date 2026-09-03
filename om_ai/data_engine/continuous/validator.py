"""
OM Dataset Validator

Checks training examples.
"""


class DatasetValidator:


    def validate(
        self,
        item: dict
    ) -> dict:


        issues=[]


        if not item.get(
            "instruction"
        ):

            issues.append(
                "missing instruction"
            )


        if not item.get(
            "response"
        ):

            issues.append(
                "missing response"
            )


        return {


            "valid":

                len(issues)==0,


            "issues":

                issues

        }