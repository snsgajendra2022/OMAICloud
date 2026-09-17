from .trace_storage import TraceStorage
from .trace_manager import TraceManager
from .event_bus import EventBus
from .metrics import AIMetrics



class ObservabilityEngine:


    def __init__(self):

        self.storage=TraceStorage()

        self.manager=TraceManager(
            self.storage
        )

        self.bus=EventBus()

        self.metrics=AIMetrics()



    def start_trace(self):

        return self.manager.create()



    def log(
        self,
        context,
        event
    ):

        self.manager.record(
            context,
            event
        )

        self.bus.publish(
            event
        )