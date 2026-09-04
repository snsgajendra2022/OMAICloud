import sqlite3



class KnowledgeGraphStore:


    def __init__(
        self,
        db="artifacts/knowledge_graph.sqlite3"
    ):

        self.conn = sqlite3.connect(db)


        self.create_tables()



    def create_tables(self):

        self.conn.execute(

        """
        CREATE TABLE IF NOT EXISTS entities
        (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,
            source TEXT
        )
        """

        )


        self.conn.execute(

        """
        CREATE TABLE IF NOT EXISTS relations
        (
            id INTEGER PRIMARY KEY,
            subject TEXT,
            relation TEXT,
            object TEXT,
            source TEXT
        )
        """

        )


        self.conn.commit()