from .conversation_manager import ConversationManager
class ConversationEngine:
    def __init__(self):self.manager=ConversationManager()
    def process(self,message,**kwargs):return self.manager.analyze(message,**kwargs)
    def record_assistant(self,state,answer):self.manager.record_assistant(state,answer)
