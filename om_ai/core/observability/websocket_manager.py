from __future__ import annotations



class WebSocketManager:


    def __init__(self):

        self.connections=set()



    async def connect(
        self,
        websocket
    ):

        await websocket.accept()

        self.connections.add(
            websocket
        )



    def disconnect(
        self,
        websocket
    ):

        self.connections.discard(
            websocket
        )



    async def broadcast(
        self,
        data
    ):


        dead=[]


        for ws in self.connections:

            try:

                await ws.send_json(
                    data
                )


            except Exception:

                dead.append(ws)



        for ws in dead:

            self.disconnect(
                ws
            )