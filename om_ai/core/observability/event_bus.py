class EventBus:


    def __init__(self):

        self.listeners=[]



    def subscribe(
        self,
        callback
    ):

        self.listeners.append(
            callback
        )



    def publish(
        self,
        event
    ):

        for listener in self.listeners:

            listener(event)