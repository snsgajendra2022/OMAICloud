"""
OM System Event Tracker
"""



from datetime import datetime





class EventTracker:



    def __init__(self):

        self.events=[]




    def emit(

        self,

        event:str,

        data:dict=None

    ):


        item={


            "event":

                event,


            "data":

                data or {},


            "time":

                datetime.utcnow().isoformat()

        }


        self.events.append(item)


        return item




    def latest(

        self,

        limit=50

    ):


        return self.events[-limit:]