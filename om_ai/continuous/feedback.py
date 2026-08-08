from __future__ import annotations
from pathlib import Path
import sqlite3,time,uuid

class FeedbackStore:
    def __init__(self,path="artifacts/feedback.sqlite3"):
        self.path=path;Path(path).parent.mkdir(parents=True,exist_ok=True);self._init()
    def _conn(self): return sqlite3.connect(self.path)
    def _init(self):
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS feedback(id TEXT PRIMARY KEY, ts REAL, user_id TEXT, prompt TEXT, response TEXT, rating INTEGER, preferred_response TEXT, metadata TEXT)")
    def add(self,prompt,response,rating,user_id="",preferred_response="",metadata=""):
        fid=str(uuid.uuid4())
        with self._conn() as c:c.execute("INSERT INTO feedback VALUES(?,?,?,?,?,?,?,?)",(fid,time.time(),user_id,prompt,response,int(rating),preferred_response,metadata))
        return fid
    def rows(self,min_rating=None):
        q="SELECT id,ts,user_id,prompt,response,rating,preferred_response,metadata FROM feedback"; params=[]
        if min_rating is not None:q+=" WHERE rating>=?";params=[int(min_rating)]
        with self._conn() as c:return c.execute(q,params).fetchall()
