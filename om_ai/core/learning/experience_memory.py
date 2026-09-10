import sqlite3
import json


class ExperienceMemory:


    def __init__(
        self,
        db="artifacts/om_experience.db"
    ):

        self.conn = sqlite3.connect(
            db
        )

        self.create()


    def create(self):

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS experiences(

                id INTEGER PRIMARY KEY,

                input TEXT,

                output TEXT,

                score REAL,

                metadata TEXT

            )
            """
        )

        self.conn.commit()



    def store(
        self,
        user_input,
        output,
        score,
        metadata=None
    ):

        self.conn.execute(
            """
            INSERT INTO experiences
            VALUES(
                NULL,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                user_input,
                output,
                score,
                json.dumps(
                    metadata or {}
                )
            )
        )

        self.conn.commit()



    def recent(
        self,
        limit=10
    ):

        rows=self.conn.execute(
            """
            SELECT *
            FROM experiences
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()


        return rows