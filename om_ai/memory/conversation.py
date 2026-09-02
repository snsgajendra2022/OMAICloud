"""
OM-1.0 Conversation Memory

Stores and retrieves conversation history.

Purpose:

- Keep chat context
- Maintain previous questions
- Provide context to reasoning engine
"""


from __future__ import annotations


from dataclasses import dataclass, field

from datetime import datetime

from typing import Any



@dataclass(slots=True)
class Message:

    role: str

    content: str

    timestamp: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )



class ConversationMemory:



    def __init__(
        self,
        max_messages: int = 50
    ):

        self.max_messages = max_messages

        self.messages: list[Message] = []



    def add_user_message(
        self,
        content: str
    ):

        self.messages.append(

            Message(

                role="user",

                content=content

            )

        )

        self._limit()



    def add_assistant_message(
        self,
        content: str
    ):

        self.messages.append(

            Message(

                role="assistant",

                content=content

            )

        )

        self._limit()



    def _limit(self):

        if len(self.messages) > self.max_messages:

            self.messages = self.messages[
                -self.max_messages:
            ]



    def get_messages(
        self
    ) -> list[dict[str, Any]]:


        return [

            {

                "role": item.role,

                "content": item.content,

                "timestamp": item.timestamp

            }

            for item in self.messages

        ]



    def get_context(
        self,
        limit: int = 10
    ) -> str:


        recent = self.messages[-limit:]


        return "\n".join(

            f"{m.role}: {m.content}"

            for m in recent

        )



    def clear(self):

        self.messages.clear()