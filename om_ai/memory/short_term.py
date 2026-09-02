"""
OM Short Term Memory

Stores current reasoning context.
"""


from __future__ import annotations

from dataclasses import dataclass, field

from typing import Any



@dataclass
class ShortTermMemory:


    context: dict[str, Any] = field(
        default_factory=dict
    )


    def remember(
        self,
        key: str,
        value: Any
    ):

        self.context[key] = value



    def recall(
        self,
        key: str,
        default=None
    ):

        return self.context.get(
            key,
            default
        )



    def clear(self):

        self.context.clear()



    def all(self):

        return self.context.copy()