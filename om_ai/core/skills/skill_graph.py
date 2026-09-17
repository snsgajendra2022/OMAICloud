from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class SkillNode:

    """
    Represents an ability.

    Example:

    React
       |
       |
    State Management
    """

    id: str

    name: str

    domain: str

    dependencies: list[str] = field(
        default_factory=list
    )

    capabilities: list[str] = field(
        default_factory=list
    )



class SkillGraph:


    def __init__(self):

        self.skills = {}



    def add_skill(
        self,
        skill: SkillNode
    ):

        self.skills[
            skill.id
        ] = skill



    def get_skill(
        self,
        skill_id: str
    ):

        return self.skills.get(
            skill_id
        )



    def dependencies(
        self,
        skill_id: str
    ):


        skill = self.get_skill(
            skill_id
        )


        if not skill:

            return []


        return skill.dependencies