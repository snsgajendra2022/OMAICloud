from __future__ import annotations

from datetime import datetime


class ContextMemory:


    def __init__(self):

        self.messages = []



    def add(
        self,
        role:str,
        content:str
    ):

        self.messages.append({

            "role":role,

            "content":content,

            "time":
                datetime.utcnow().isoformat()

        })



    def all(self):

        return self.messages



    def clear(self):

        self.messages.clear()