"""
OM Autonomous Hardware Design Manager
"""


from .requirement import RequirementAnalyzer

from .architecture import HardwareArchitecture

from .component import ComponentSelector

from .circuit import CircuitDesigner

from .simulation import HardwareSimulator

from .optimization import HardwareOptimizer

from .validation import HardwareValidator

from .memory import HardwareDesignMemory





class HardwareDesignManager:


    def __init__(self):


        self.requirement = RequirementAnalyzer()

        self.architecture = HardwareArchitecture()

        self.components = ComponentSelector()

        self.circuit = CircuitDesigner()

        self.simulator = HardwareSimulator()

        self.optimizer = HardwareOptimizer()

        self.validator = HardwareValidator()

        self.memory = HardwareDesignMemory()



    def design(

        self,

        request

    ):


        requirement=self.requirement.analyze(

            request

        )


        architecture=self.architecture.design(

            requirement

        )


        components=self.components.select(

            architecture

        )


        circuit=self.circuit.create(

            components

        )


        simulation=self.simulator.simulate(

            circuit

        )


        optimization=self.optimizer.optimize(

            simulation

        )


        validation=self.validator.validate(

            circuit

        )


        result={


            "requirement":

                requirement,


            "architecture":

                architecture,


            "components":

                components,


            "circuit":

                circuit,


            "simulation":

                simulation,


            "optimization":

                optimization,


            "validation":

                validation

        }


        self.memory.store(

            result

        )


        return result