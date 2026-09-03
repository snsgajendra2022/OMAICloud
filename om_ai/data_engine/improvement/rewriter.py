"""
OM Dataset Sample Rewriter

Improves weak samples.
"""



class SampleRewriter:



    def rewrite(
        self,
        item:dict,
        problems:list[str]
    ) -> dict:



        updated = dict(item)



        if "missing_instruction" in problems:

            updated["instruction"] = (

                "Provide a detailed solution"

            )



        if "missing_response" in problems:


            updated["response"] = (

                "A complete explanation "
                "with implementation details "
                "is required."

            )



        if "short_answer" in problems:


            updated["response"] += (

                " Include architecture, "
                "implementation steps, "
                "validation and best practices."

            )



        updated["improved"] = True


        updated["improvement_reason"] = problems



        return updated