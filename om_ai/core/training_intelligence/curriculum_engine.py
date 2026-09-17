from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib



@dataclass
class CurriculumItem:
    """
    Dynamic learning unit.
    """

    concept_id: str

    concept: str

    domain: str

    level: str

    prerequisites: list[str] = field(
        default_factory=list
    )

    skills: list[str] = field(
        default_factory=list
    )

    objectives: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )



class CurriculumEngine:
    """
    OM Adaptive Curriculum Intelligence.

    Uses:

    - Knowledge Graph
    - Dependency Resolver
    - Skill Intelligence

    No fixed topic database.
    """


    def __init__(
        self,
        knowledge_graph=None,
        dependency_resolver=None,
    ):

        self.graph = knowledge_graph

        self.dependency_resolver = (
            dependency_resolver
        )



    def generate_id(
        self,
        value: str
    ):

        return hashlib.sha256(
            value.encode(
                "utf-8"
            )
        ).hexdigest()[:16]



    def detect_level(
        self,
        dependency_count: int
    ):

        """
        Dynamic difficulty calculation.

        Based on concept dependency depth.
        """

        if dependency_count == 0:

            return "foundation"


        if dependency_count <= 2:

            return "intermediate"


        if dependency_count <= 5:

            return "advanced"


        return "expert"



    def create_curriculum_item(
        self,
        node,
    ):


        prerequisites = []


        if self.dependency_resolver:


            prerequisites = (
                self.dependency_resolver.resolve(
                    node.id
                )
            )


        level = self.detect_level(
            len(prerequisites)
        )


        return CurriculumItem(

            concept_id=node.id,

            concept=node.name,

            domain=node.domain,

            level=level,

            prerequisites=prerequisites,

            skills=node.skills,

            objectives=[

                f"Understand {node.name}",

                f"Apply {node.name} practically",

                f"Debug problems involving {node.name}",

                f"Design solutions using {node.name}",

            ],

            metadata={

                "generated_by":
                    "OM Curriculum Intelligence",

                "dependency_depth":
                    len(prerequisites)

            }

        )



    def build_for_concept(
        self,
        concept_id: str
    ):


        if not self.graph:

            return []



        node = (
            self.graph.get_node(
                concept_id
            )
        )


        if not node:

            return []



        curriculum=[]


        dependencies=[]


        if self.dependency_resolver:

            dependencies = (
                self.dependency_resolver.resolve(
                    concept_id
                )
            )


        for dependency in dependencies:


            dep_node = (
                self.graph.get_node(
                    dependency
                )
            )


            if dep_node:

                curriculum.append(

                    self.create_curriculum_item(
                        dep_node
                    )

                )



        curriculum.append(

            self.create_curriculum_item(
                node
            )

        )


        return curriculum



    def build_domain_path(
        self,
        domain: str
    ):


        result=[]


        if not self.graph:

            return result



        for node in (
            self.graph.nodes.values()
        ):


            if node.domain == domain:


                result.append(

                    self.create_curriculum_item(
                        node
                    )

                )


        return result