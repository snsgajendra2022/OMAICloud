import sqlite3
from .memory_item import MemoryItem

class MemoryStore:


    def __init__(
        self,
        db_path="artifacts/memory.sqlite3"
    ):

        self.connection = sqlite3.connect(
            db_path
        )

        self.create_tables()



    def create_tables(self):

        self.connection.execute(
        """
        CREATE TABLE IF NOT EXISTS memories
        (
            id INTEGER PRIMARY KEY,

            memory_type TEXT,

            content TEXT,

            importance INTEGER,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
        )


        self.connection.commit()



    def save(
        self,
        memory_type,
        content,
        importance=1
    ):


        self.connection.execute(
        """
        INSERT INTO memories
        (
            memory_type,
            content,
            importance
        )

        VALUES (?, ?, ?)

        """,
        (
            memory_type,
            content,
            importance
        )
        )


        self.connection.commit()



    def search(
        self,
        memory_type=None
    ):


        if memory_type:


            result = self.connection.execute(
            """
            SELECT *
            FROM memories
            WHERE memory_type=?

            """,
            (
                memory_type,
            )
            )


        else:

            result = self.connection.execute(
            """
            SELECT *
            FROM memories

            """
            )


        return result.fetchall()

    def __init__(self):

        self.memories = []



    def save(
        self,
        memory: MemoryItem
    ):

        self.memories.append(
            memory
        )



    def all(self):

        return self.memories



    def search(
        self,
        keyword
    ):

        results=[]


        for memory in self.memories:

            if keyword.lower() in (
                memory.content.lower()
            ):

                results.append(
                    memory
                )


        return results