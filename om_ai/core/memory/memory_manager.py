from .memory_store import MemoryStore

from .short_term_memory import ShortTermMemory

from .long_term_memory import LongTermMemory

from .episodic_memory import EpisodicMemory

from .semantic_memory import SemanticMemory

from .experience_memory import ExperienceMemory

from .memory_item import MemoryItem
from .experience_analyzer import ExperienceAnalyzer
from .memory_evaluator import MemoryEvaluator
from .memory_retriever import MemoryRetriever



class MemoryManager:


    def __init__(self):


        self.store = MemoryStore()

        self.analyzer = ExperienceAnalyzer()

        self.evaluator = MemoryEvaluator()

        self.retriever = MemoryRetriever()

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
        
    def process(
        self,
        message
    ):


        experiences = (
            self.analyzer.analyze(
                message
            )
        )


        saved=[]


        for exp in experiences:


            if self.evaluator.should_store(
                exp
            ):


                memory = MemoryItem(

                    content=
                    exp["content"],

                    memory_type=
                    exp["type"],

                    importance=
                    0.8

                )


                self.store.save(
                    memory
                )


                saved.append(
                    memory
                )



        return saved



    def recall(
        self,
        query
    ):


        return self.retriever.retrieve(
            query,
            self.store
        )