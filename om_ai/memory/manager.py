"""
OM Memory Manager

Controls:

- Store
- Recall
- Long term memory
"""


from om_ai.memory.storage import MemoryStorage
from om_ai.memory.models import MemoryItem
from om_ai.memory.extractor import MemoryExtractor
from om_ai.memory.semantic_search import SemanticMemorySearch
from om_ai.memory.project_extractor import ProjectMemoryExtractor
from om_ai.memory.experience import Experience

class MemoryManager:


    def __init__(self):

        self.storage = MemoryStorage()
        self.extractor = MemoryExtractor()
        self.semantic = SemanticMemorySearch()
        self.project_extractor = ProjectMemoryExtractor()

    def remember_conversation(
        self,
        question,
        answer
    ):


        text = str(question)


        extracted = self.extractor.extract(
            text
        )


        for item in extracted:


            self.storage.save(

                MemoryItem(

                    id=None,

                    content=item,

                    memory_type="long_term",

                    importance=0.8

                )

            )



    def get_context(
        self
    ):


        memories = self.storage.all()


        return [

            row[1]

            for row in memories[:20]

        ]
    def get_relevant_memory(
        self,
        question: str,
        memories: list | None = None
    ):
      if memories is None:
 
         memories = self.get_context()
      return self.semantic.search(
            question,
            memories
        )

    def remember_project(
    self,
    project,
    description
    ):

     self.storage.save(

        MemoryItem(

            id=None,

            content=description,

            memory_type="project",

            project=project,

            importance=0.9

        )

       )
    def remember_experience(
        self,
        question,
        solution,
        score
    ):

     self.storage.save(

        MemoryItem(

            id=None,

            content=(
                question
                +
                "\n"
                +
                solution
            ),

            memory_type="experience",
            importance=score

        )

    )