from .memory_store import MemoryStore

from .short_term_memory import ShortTermMemory

from .long_term_memory import LongTermMemory

from .episodic_memory import EpisodicMemory

from .semantic_memory import SemanticMemory

from .experience_memory import ExperienceMemory



class MemoryManager:


    def __init__(self):


        self.store = MemoryStore()


        self.short_term = ShortTermMemory()


        self.long_term = LongTermMemory(
            self.store
        )


        self.episodic = EpisodicMemory(
            self.store
        )


        self.semantic = SemanticMemory(
            self.store
        )


        self.experience = ExperienceMemory(
            self.store
        )



    def remember(
        self,
        text
    ):

        self.short_term.add(
            text
        )


        self.experience.save_experience(
            text
        )



    def recall(self):

        return {

            "conversation":
                self.short_term.get(),

            "long_term":
                self.long_term.recall()

        }