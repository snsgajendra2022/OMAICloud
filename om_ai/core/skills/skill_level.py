from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SkillLevel:

    """
    Represents skill mastery level.
    """

    name: str

    score: float


LEVELS = {

    "novice": 20,

    "foundation": 40,

    "intermediate": 60,

    "advanced": 75,

    "expert": 90,

    "master": 100,

}



def calculate_level(
    score: float
) -> SkillLevel:


    selected = "novice"


    for name, threshold in LEVELS.items():

        if score >= threshold:

            selected = name


    return SkillLevel(

        name=selected,

        score=score

    )