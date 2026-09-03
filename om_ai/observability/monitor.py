"""
OM Self Monitoring Engine
"""


from .metrics import MetricsCollector

from .events import EventTracker

from .health import HealthMonitor

from .analyzer import PerformanceAnalyzer





class OMMonitor:



    def __init__(self):


        self.metrics=MetricsCollector()

        self.events=EventTracker()

        self.health=HealthMonitor()

        self.analyzer=PerformanceAnalyzer()




    def execution_started(

        self,

        agent=None

    ):


        self.metrics.increment(

            "executions"

        )


        self.events.emit(

            "execution_started",

            {

                "agent":

                    agent

            }

        )





    def execution_failed(

        self,

        error

    ):


        self.metrics.increment(

            "errors"

        )


        self.events.emit(

            "execution_failed",

            {

                "error":

                    str(error)

            }

        )





    def status(self):


        metrics=self.metrics.get_all()



        return {


            "health":

                self.health.check(

                    metrics

                ),


            "performance":

                self.analyzer.analyze(

                    metrics,

                    self.events.latest()

                ),


            "events":

                self.events.latest()

        }