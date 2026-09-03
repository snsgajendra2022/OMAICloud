"""
OM Autonomous Software Engineering Agent
"""


from om_ai.code_intelligence import CodeUnderstandingEngine


from .planner import ChangePlanner

from .file_selector import FileSelector

from .modifier import CodeModifier

from .reviewer import CodeReviewer

from .memory import EngineeringMemory





class SoftwareEngineeringAgent:



    def __init__(self):


        self.code_engine = CodeUnderstandingEngine()

        self.planner = ChangePlanner()

        self.selector = FileSelector()

        self.modifier = CodeModifier()

        self.reviewer = CodeReviewer()

        self.memory = EngineeringMemory()




    def analyze_project(

        self,

        repository,

        requirement

    ):


        codebase=self.code_engine.analyze(

            repository

        )



        plan=self.planner.plan(

            requirement,

            codebase

        )



        files=self.selector.select(

            codebase["files"],

            requirement

        )



        changes=[]



        for file in files:


            changes.append(

                self.modifier.generate_change(

                    file["file"],

                    requirement

                )

            )



        review=self.reviewer.review(

            changes

        )



        result={


            "requirement":

                requirement,


            "plan":

                plan,


            "files":

                files,


            "changes":

                changes,


            "review":

                review

        }



        self.memory.store(

            result

        )



        return result