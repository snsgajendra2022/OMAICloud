import re
class MessageRelationDetector:
    def detect(self,message,history=None,state=None):
        t=(message or "").strip(); l=t.lower(); h=history or []
        if re.match(r"^(yes|yeah|yep|sure|okay|ok|done|go ahead|please do)\b",l) and (getattr(state,"last_assistant_question","") or getattr(state,"last_assistant_message","")): return {"relation":"confirmation","confidence":.97}
        if re.match(r"^(no|nope|not really|don't|do not)\b",l) and getattr(state,"last_assistant_question",""): return {"relation":"rejection","confidence":.95}
        if re.match(r"^(actually|correction|i meant|i mean)\b",l): return {"relation":"correction","confidence":.95}
        if re.search(r"\b(it|this|that|these|those|same|above|previous|earlier|again|the issue|the problem|the file|the code)\b",l) and (h or getattr(state,"current_topic","")): return {"relation":"reference_to_past","confidence":.92}
        if re.match(r"^(and|also|then|what about|how about|continue|more|another|next)\b",l) and h: return {"relation":"follow_up","confidence":.90}
        if len(t.split())<=8 and h: return {"relation":"answer_to_previous" if getattr(state,"last_assistant_question","") else "continuation","confidence":.82}
        q=self._tokens(t); x=set()
        for m in h[-6:]: x|=self._tokens(str(m.get("content") or ""))
        if q and q&x:return {"relation":"continuation","confidence":.78}
        if q and x and not q&x:return {"relation":"topic_switch","confidence":.86}
        return {"relation":"new_topic","confidence":.72}
    def _tokens(self,s): return {x for x in re.findall(r"[a-zA-Z0-9_+#.-]{2,}",s.lower()) if x not in {"the","and","this","that","with","from","what","how","why","are","you","for"}}
