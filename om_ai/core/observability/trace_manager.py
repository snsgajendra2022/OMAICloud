from .trace_context import TraceContext


class TraceManager:


    def __init__(
        self,
        storage
    ):

        self.storage=storage



    def create(
        self
    ):

        return TraceContext()



    def record(
        self,
        context,
        event
    ):

        context.add(
            event
        )

        self.storage.save(
            event
        )