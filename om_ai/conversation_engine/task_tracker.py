import re
class TaskTracker:
    def update(self,message,topic,relation,state):
        t=(message or "").strip(); active=getattr(state,"active_task",""); goal=getattr(state,"active_goal","")
        if re.search(r"\b(fix|build|create|implement|debug|check|explain|compare|find|write|update|add|remove|configure|deploy)\b",t,re.I) or relation=="topic_switch": active=t[:240]; goal=t[:300]
        elif not active and topic: active=f"Work on {topic}"; goal=active
        return active,goal
