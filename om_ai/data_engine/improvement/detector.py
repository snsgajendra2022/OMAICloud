"""
OM Dataset Problem Detector

Finds weak training samples.
"""



class DatasetProblemDetector:



    def detect(
        self,
        item:dict
    ) -> list[str]:


        problems=[]


        instruction = item.get(
            "instruction",
            ""
        )


        response = item.get(
            "response",
            ""
        )



        if not instruction.strip():

            problems.append(
                "missing_instruction"
            )


        if not response.strip():

            problems.append(
                "missing_response"
            )


        if len(response.split()) < 5:

            problems.append(
                "short_answer"
            )


        if "error" in response.lower():

            problems.append(
                "contains_error"
            )


        return problems