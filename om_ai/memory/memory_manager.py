"""
OM Memory Manager

Controls all memory layers.
"""


from om_ai.memory.short_term import ShortTermMemory
from om_ai.memory.conversation import ConversationMemory
from om_ai.memory.project_memory import ProjectMemory
from om_ai.memory.long_term import LongTermMemory



class MemoryManager:


    def __init__(self):

        self.short_term = ShortTermMemory()

        self.conversation = ConversationMemory()

        self.project = ProjectMemory()

        self.long_term = LongTermMemory()



    def remember_conversation(
        self,
        user,
        assistant
    ):

        self.conversation.add_user_message(user)

        self.conversation.add_assistant_message(
            assistant
        )



    def get_context(self):

        return {

            "short_term":
                self.short_term.all(),

            "conversation":
                self.conversation.get_context(),

            "projects":
                self.project.data,

            "long_term":
                self.long_term.memory

        }