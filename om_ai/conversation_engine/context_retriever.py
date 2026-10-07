import re
class ContextRetriever:
    STOP={"the","and","that","this","with","from","what","how","why","are","you","for","about","please"}
    def retrieve(self,message,history=None,memory=None,limit=6):
        h=list(history or []); q=self._tokens(message); scored=[]
        for i,m in enumerate(h):
            c=str(m.get("content") or ""); scored.append((len(q&self._tokens(c))*2+(i+1)/max(len(h),1),m))
        scored.sort(key=lambda x:x[0],reverse=True); hits=[]
        if memory:
            try: hits=memory.recall(message,k=limit) or []
            except Exception: pass
        return {"history":[m for _,m in scored[:limit]],"memory":hits}
    def _tokens(self,s): return {x for x in re.findall(r"[a-zA-Z0-9_+#.-]{2,}",(s or "").lower()) if x not in self.STOP}
