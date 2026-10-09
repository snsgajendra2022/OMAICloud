import re
class TopicTracker:
    def infer(self,message,current=""):
        for n,p in [("react",r"\breact\b"),("angular",r"\bangular\b"),("python",r"\bpython\b"),("javascript",r"\bjavascript|typescript\b"),("sql",r"\bsql|database|mysql|postgres\b"),("github",r"\bgithub|git\b"),("android",r"\bandroid|capacitor|ionic\b"),("ios",r"\bios|xcode|swift\b"),("tokenizer",r"\btokenizer|checkpoint|vocab\b"),("model-runtime",r"\bmodelgateway|inference|generation\b")]:
            if re.search(p,message or "",re.I): return n
        return current
    def entities(self,message):
        out={}
        for k,p in [("technology",r"\b(React|Angular|Python|TypeScript|JavaScript|SQL|Android|iOS|Ionic|Capacitor)\b"),("problem",r"\b(white screen|blank page|undefined|exception|crash|not working|error|bug)\b")]:
            m=re.search(p,message or "",re.I)
            if m: out[k]=m.group(1)
        return out
