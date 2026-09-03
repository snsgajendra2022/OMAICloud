"""
OM Autonomous Improvement Engine
"""


from .analyzer import ReflectionAnalyzer

from .reflector import Reflector

from .strategy import StrategyMemory





class ReflectionEngine:



    def __init__(self):


        self.analyzer = ReflectionAnalyzer()

        self.reflector = Reflector()

        self.memory = StrategyMemory()




    def process(

        self,

        execution:dict,

        evaluation:dict | None = None

    ):


        analysis=self.analyzer.analyze(

            execution,

            evaluation

        )



        reflection=self.reflector.reflect(

            analysis

        )



        if reflection["improvements"]:


            self.memory.save(

                reflection

            )



        return {


            "analysis":

                analysis,


            "reflection":

                reflection

        }