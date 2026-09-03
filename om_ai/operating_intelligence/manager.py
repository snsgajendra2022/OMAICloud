"""
OM Operating Intelligence Manager

Main integration layer.
"""


from .core import OMCore

from .module_registry import ModuleRegistry

from .orchestrator import OMOrchestrator

from .state import OMState

from .health import OMHealth

from .memory import OMMemory





class OMOperatingManager:



    def __init__(self):


        self.core = OMCore()

        self.registry = ModuleRegistry()

        self.orchestrator = OMOrchestrator()

        self.state = OMState()

        self.health = OMHealth()

        self.memory = OMMemory()



    def register_module(

        self,

        name,

        module

    ):


        self.core.register(

            name,

            module

        )


        self.registry.add(

            name

        )



    def run(

        self,

        task

    ):


        result=self.orchestrator.execute(

            task,

            self.core.modules

        )


        self.memory.store(

            result

        )


        return result



    def status(self):


        return {


            "state":

                self.state.get(),


            "health":

                self.health.check(

                    self.core.modules

                ),


            "modules":

                self.registry.all()

        }