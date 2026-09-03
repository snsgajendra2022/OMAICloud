"""
OM Digital Twin Manager
"""


from .twin import DigitalTwin

from .simulator import TwinSimulator

from .prediction import TwinPrediction

from .optimizer import TwinOptimizer

from .memory import TwinMemory





class DigitalTwinManager:



    def __init__(self):


        self.twin=DigitalTwin()

        self.simulator=TwinSimulator()

        self.prediction=TwinPrediction()

        self.optimizer=TwinOptimizer()

        self.memory=TwinMemory()



    def analyze(

        self,

        entity,

        change

    ):


        self.twin.register(

            entity

        )


        simulation=self.simulator.simulate(

            self.twin,

            change

        )


        prediction=self.prediction.predict(

            simulation

        )


        optimization=self.optimizer.optimize(

            simulation

        )


        result={


            "simulation":

                simulation,


            "prediction":

                prediction,


            "optimization":

                optimization

        }


        self.memory.store(

            result

        )


        return result