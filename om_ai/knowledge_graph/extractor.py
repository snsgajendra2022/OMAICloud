"""
OM Concept Extraction Engine
"""


from .entity import Entity

from .relation import Relationship





class ConceptExtractor:



    def extract(
        self,
        text:str
    ):


        entities=[]

        relations=[]


        words=text.split()



        technologies=[

            "python",

            "java",

            "php",

            "laravel",

            "react",

            "mysql",

            "docker",

            "api",

            "database"

        ]



        found=[]


        for word in words:


            clean=word.lower().strip(
                ".,()"
            )


            if clean in technologies:

                found.append(clean)



        for item in found:


            entities.append(

                Entity(

                    name=item,

                    entity_type="technology"

                )

            )



        for i in range(
            len(found)-1
        ):


            relations.append(

                Relationship(

                    source=found[i],

                    relation="related_to",

                    target=found[i+1]

                )

            )


        return {


            "entities":

                entities,


            "relations":

                relations

        }