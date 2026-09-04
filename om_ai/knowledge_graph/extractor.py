"""
OM Advanced Entity Extraction Engine

Responsible for:

- Entity Detection
- Entity Classification
- Relationship Discovery
- Confidence Scoring
- Knowledge Graph Preparation

"""


from dataclasses import dataclass, field

import re





@dataclass
class ExtractedEntity:


    name: str


    entity_type: str


    confidence: float = 0.0


    context: str = ""



    def to_dict(self):

        return {

            "name":

                self.name,


            "type":

                self.entity_type,


            "confidence":

                self.confidence,


            "context":

                self.context

        }





class EntityExtractor:



    ENTITY_RULES = {


        "technology":

        [

            "python",

            "php",

            "laravel",

            "react",

            "react native",

            "django",

            "node",

            "mysql",

            "postgresql",

            "mongodb",

            "docker",

            "kubernetes"

        ],



        "framework":

        [

            "laravel",

            "django",

            "spring",

            "flutter",

            "angular"

        ],



        "database":

        [

            "mysql",

            "postgresql",

            "mongodb",

            "sqlite",

            "redis"

        ],



        "company":

        [

            "google",

            "openai",

            "microsoft",

            "meta"

        ],



        "ai_concept":

        [

            "machine learning",

            "deep learning",

            "neural network",

            "llm",

            "transformer",

            "rag"

        ]

    }



    def extract(

        self,

        text:str

    ):



        entities=[]


        lower=text.lower()



        # Rule based extraction

        for entity_type, values in self.ENTITY_RULES.items():


            for value in values:


                if value in lower:


                    entities.append(

                        ExtractedEntity(

                            name=value,

                            entity_type=entity_type,

                            confidence=0.95,

                            context=self._context(

                                text,

                                value

                            )

                        )

                    )



        # Named entity fallback

        names=re.findall(

            r"\b[A-Z][a-zA-Z0-9]+\b",

            text

        )



        for name in names:


            if not any(

                x.name.lower()==name.lower()

                for x in entities

            ):


                entities.append(

                    ExtractedEntity(

                        name=name,

                        entity_type="concept",

                        confidence=0.60,

                        context=self._context(

                            text,

                            name

                        )

                    )

                )



        return [

            entity.to_dict()

            for entity in entities

        ]





    def _context(

        self,

        text,

        keyword

    ):


        index=text.lower().find(

            keyword.lower()

        )



        if index == -1:

            return ""



        start=max(

            0,

            index-50

        )


        end=min(

            len(text),

            index+100

        )


        return text[start:end]

        """
OM AI Knowledge Graph Concept Extractor

Extracts entities/concepts from
documents and semantic understanding.
"""


class ConceptExtractor:


    def extract(self, data):

        concepts = []


        if isinstance(data, dict):

            for key, value in data.items():

                concepts.append(
                    {
                        "name": str(value),
                        "type": key
                    }
                )


        elif isinstance(data, str):

            words = data.split()

            for word in words:

                concepts.append(
                    {
                        "name": word,
                        "type": "concept"
                    }
                )


        return concepts