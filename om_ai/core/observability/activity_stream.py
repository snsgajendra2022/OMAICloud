from __future__ import annotations

import asyncio



class ActivityStream:


    def __init__(self):

        self.subscribers=[]



    def subscribe(
        self,
        callback
    ):

        self.subscribers.append(
            callback
        )



    async def publish(
        self,
        event
    ):


        for subscriber in self.subscribers:

            result = subscriber(event)


            if asyncio.iscoroutine(result):

                await result