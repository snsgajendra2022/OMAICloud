"""
OM Context Builder

Combines all intelligence sources.
"""





class ContextBuilder:



    def build(

        self,

        *,

        question,

        agent=None,

        memory=None,

        knowledge=None,

        tools=None

    ):


        return {


            "question":

                question,


            "agent":

                agent or {},


            "memory":

                memory or {},


            "knowledge":

                knowledge or [],


            "tools":

                tools or []

        }