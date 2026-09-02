"""
OM Persistent Memory Storage

SQLite based memory database.
"""


from pathlib import Path

import sqlite3



class MemoryStorage:


    def __init__(
        self,
        path="data/om-memory/memory.db"
    ):

        Path(path).parent.mkdir(
            parents=True,
            exist_ok=True
        )


        self.conn = sqlite3.connect(
            path
        )


        self.create_tables()



    def create_tables(self):

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                content TEXT NOT NULL,

                memory_type TEXT,

                project TEXT,

                tags TEXT,

                importance REAL,

                created_at TEXT
            )
            """
        )


        self.conn.commit()



    def save(
        self,
        memory
    ):


        cursor = self.conn.cursor()


        cursor.execute(

            """
            INSERT INTO memories
            (
                content,
                memory_type,
                importance,
                created_at
            )

            VALUES
            (?,?,?,?)
            """,

            (
                memory.content,
                memory.memory_type,
                memory.importance,
                memory.created_at
            )

        )


        self.conn.commit()


        return cursor.lastrowid



    def all(self):

        rows = self.conn.execute(

            """
            SELECT *
            FROM memories
            ORDER BY id DESC
            """

        ).fetchall()


        return rows