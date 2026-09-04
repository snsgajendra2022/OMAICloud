from dataclasses import dataclass


@dataclass
class Entity:

    name: str

    entity_type: str

    source: str



@dataclass
class Relation:

    subject: str

    relation: str

    object: str

    source: str