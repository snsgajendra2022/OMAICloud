"""
OM Self Healing Execution Engine
"""


from .analyzer import FailureAnalyzer

from .root_cause import RootCauseAnalyzer

from .strategy import RecoveryStrategy

from .memory import FailureMemory





class SelfHealingEngine:



    def __init__(self):


        self.analyzer = FailureAnalyzer()

        self.root = RootCauseAnalyzer()

        self.strategy = RecoveryStrategy()

        self.memory = FailureMemory()




    def recover(

        self,

        task,

        error,

        agent=""

    ):


        failure={

            "task":

                task,

            "error":

                error,

            "agent":

                agent

        }



        analysis=self.analyzer.analyze(

            failure

        )


        cause=self.root.detect(

            analysis

        )


        recovery=self.strategy.generate(

            cause

        )



        result={


            "failure":

                failure,


            "analysis":

                analysis,


            "root_cause":

                cause,


            "recovery_plan":

                recovery

        }



        self.memory.store(

            result

        )



        return result