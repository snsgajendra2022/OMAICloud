"""
OM Agent Communication Bus

Handles agent-to-agent messages.
"""


from .message import AgentMessage





class CommunicationBus:



    def __init__(self):

        self.messages=[]



    def send(

        self,

        sender:str,

        receiver:str,

        message:str,

        message_type="information",

        metadata=None

    ):


        msg=AgentMessage(

            sender=sender,

            receiver=receiver,

            message=message,

            message_type=message_type,

            metadata=metadata or {}

        )


        self.messages.append(

            msg

        )


        return msg.to_dict()




    def receive(

        self,

        agent:str

    ):


        return [

            msg.to_dict()

            for msg in self.messages

            if msg.receiver == agent

        ]




    def history(self):


        return [

            msg.to_dict()

            for msg in self.messages

        ]