from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class SkillProgress:


    skill_id: str


    score: float = 0


    attempts: int = 0


    successful_tasks: int = 0


    history: list[dict] = field(
        default_factory=list
    )



    def update(
        self,
        success: bool,
        quality: float
    ):


        self.attempts += 1


        if success:

            self.successful_tasks += 1



        self.score = (

            self.score * 0.7

            +

            quality * 100 * 0.3

        )


        self.history.append(

            {

                "success": success,

                "quality": quality,

            }

        )