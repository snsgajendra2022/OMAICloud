"""
OM Voice Command Analyzer
"""


class VoiceCommandAnalyzer:



    def analyze(

        self,

        text

    ):


        intent="general"



        lower=text.lower()



        if "create" in lower:

            intent="creation"



        elif "search" in lower:

            intent="search"



        elif "open" in lower:

            intent="action"



        return {


            "text":
                text,


            "intent":
                intent

        }