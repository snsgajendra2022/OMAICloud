from .conversation_router import ConversationRouter
from .social_response import SocialResponseEngine



class ConversationEngine:


    def __init__(self):

        self.router = ConversationRouter()

        self.response = SocialResponseEngine()



    def process(
        self,
        message
    ):


        intent = self.router.detect(
            message
        )


        if intent:

            return {

                "handled":True,

                "response":
                    self.response.respond(
                        intent
                    )

            }



        return {

            "handled":False

        }