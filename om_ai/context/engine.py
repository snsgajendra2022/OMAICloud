"""
OM Autonomous Context Awareness Engine
"""


from .environment import EnvironmentDetector

from .situation import SituationAnalyzer

from .analyzer import ContextAnalyzer





class ContextEngine:



    def __init__(self):


        self.environment = EnvironmentDetector()


        self.situation = SituationAnalyzer()


        self.analyzer = ContextAnalyzer()




    def understand(

        self,

        task:str,

        user=None,

        memory=None,

        project=None

    ):


        env=self.environment.detect()



        context=self.analyzer.combine(

            user or {},

            memory or {},

            project or {},

            env

        )


        context["task"]=task



        context["situation"]=self.situation.analyze(

            context

        )


        return context