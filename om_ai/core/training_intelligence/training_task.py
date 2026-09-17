from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class TrainingTask:


    capability:str


    dataset:str


    priority:float


    reason:str


    metadata:dict = field(
        default_factory=dict
    )