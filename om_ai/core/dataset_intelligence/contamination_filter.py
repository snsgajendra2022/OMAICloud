from __future__ import annotations


import re



class ContaminationFilter:
    """
    Detect unsafe training contamination.

    Detects:

    - API keys
    - secrets
    - prompt leakage
    - system instructions
    """


    patterns=[

        r"sk-[A-Za-z0-9]+",

        r"api[_-]?key",

        r"password\s*=",

        r"system prompt",

        r"developer message",

    ]



    def check(
        self,
        text: str
    ):


        findings=[]


        for pattern in self.patterns:


            if re.search(
                pattern,
                text,
                re.I
            ):

                findings.append(
                    pattern
                )


        return {

            "safe":
                len(findings)==0,

            "issues":
                findings

        }