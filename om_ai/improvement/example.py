"""
OM Training Example Model

Creates SFT training samples.
"""


from dataclasses import dataclass, field

from datetime import datetime




@dataclass
class TrainingExample:


    instruction: str


    response: str


    category: str = "general"


    quality_score: float = 0.0


    metadata: dict = field(
        default_factory=dict
    )


    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )



    def to_dict(self):

        return {

            "instruction":
                self.instruction,

            "response":
                self.response,

            "category":
                self.category,

            "quality_score":
                self.quality_score,

            "metadata":
                self.metadata,

            "created_at":
                self.created_at

        }