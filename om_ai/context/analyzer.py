"""
OM Context Analyzer
"""




class ContextAnalyzer:



    def combine(

        self,

        user,

        memory,

        project,

        environment

    ):


        return {


            "user_context":

                user,


            "memory_context":

                memory,


            "project_context":

                project,


            "environment":

                environment

        }