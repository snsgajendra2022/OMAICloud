from .context_manager import ContextManager



class LongContextEngine:


    def __init__(self):

        self.manager=ContextManager()



    def process(
        self,
        user_message
    ):


        context=self.manager.get_context(
            user_message
        )


        return {

            "message":
                user_message,

            "related_context":
                context,

            "context_available":
                len(context)>0

        }



    def store(
        self,
        role,
        content
    ):

        self.manager.remember(
            role,
            content
        )