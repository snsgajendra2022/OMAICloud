from .entity import EntityGenerator
from .relation import RelationGenerator
from .store import KnowledgeGraphStore



class KnowledgeGraphEngine:


    def __init__(self):

        self.entities = EntityGenerator()

        self.relations = RelationGenerator()

        self.store = KnowledgeGraphStore()



    def process(
        self,
        data,
        source
    ):


        entities = self.entities.create(
            data,
            source
        )


        relations = self.relations.create(
            entities,
            source
        )


        return {


            "entities":
                entities,


            "relations":
                relations

        }