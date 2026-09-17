import uuid


class TraceContext:


    def __init__(self):

        self.trace_id = str(
            uuid.uuid4()
        )


        self.events=[]



    def add(
        self,
        event
    ):

        self.events.append(
            event
        )


    def all(self):

        return self.events