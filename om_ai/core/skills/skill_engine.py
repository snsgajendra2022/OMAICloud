from __future__ import annotations


from .skill_graph import (
    SkillGraph,
    SkillNode,
)

from .skill_progress import (
    SkillProgress,
)

from .skill_level import (
    calculate_level,
)



class SkillEngine:
    """
    OM Skill Intelligence Engine.

    Converts knowledge into abilities.
    """



    def __init__(self):

        self.graph = SkillGraph()

        self.progress = {}



    def register_skill(
        self,
        skill: SkillNode
    ):


        self.graph.add_skill(
            skill
        )


        self.progress[
            skill.id
        ] = SkillProgress(

            skill_id=skill.id

        )



    def evaluate_skill(
        self,
        skill_id: str
    ):


        progress = (
            self.progress.get(
                skill_id
            )
        )


        if not progress:

            return None



        level = calculate_level(

            progress.score

        )


        return {

            "skill":

                skill_id,


            "score":

                progress.score,


            "level":

                level.name,


            "attempts":

                progress.attempts,

        }



    def update_skill(
        self,
        skill_id: str,
        success: bool,
        quality: float
    ):


        progress = (
            self.progress.get(
                skill_id
            )
        )


        if progress:

            progress.update(

                success,

                quality

            )



    def recommend_learning(
        self,
        skill_id: str
    ):


        return (

            self.graph.dependencies(

                skill_id

            )

        )