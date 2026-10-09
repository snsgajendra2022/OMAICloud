import re
class ReferenceResolver:
    PAT=re.compile(r"\b(it|this|that|these|those|same|above|previous|earlier|again|the issue|the problem|the file|the code)\b",re.I)
    def resolve(self,message,state,relevant):
        if not self.PAT.search(message or ""): return []
        target=getattr(state,"active_task","") or getattr(state,"active_goal","") or getattr(state,"last_user_message","") or getattr(state,"last_assistant_message","")
        return [{"reference":m.group(1),"target":target[:600]} for m in self.PAT.finditer(message or "") if target]
