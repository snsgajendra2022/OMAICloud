from collections import defaultdict
from .conversation_state import ConversationState,ConversationTurn
from .message_relation import MessageRelationDetector
from .topic_tracker import TopicTracker
from .task_tracker import TaskTracker
from .reference_resolver import ReferenceResolver
from .context_retriever import ContextRetriever
class ConversationManager:
    def __init__(self):
        self.states=defaultdict(lambda:ConversationState(""));self.relations=MessageRelationDetector();self.topics=TopicTracker();self.tasks=TaskTracker();self.refs=ReferenceResolver();self.retriever=ContextRetriever()
    def analyze(self,message,history=None,tenant_id="default",actor="",conversation_id=None,durable_memory=None):
        key=f"{tenant_id}:{actor or 'anon'}:{conversation_id or 'default'}";s=self.states[key]
        if not s.conversation_id:s.conversation_id=conversation_id or key
        if history:
            s.recent_messages=[]
            for m in history[-24:]:s.add(ConversationTurn(str(m.get("role") or "user"),str(m.get("content") or "")))
            for t in reversed(s.recent_messages):
                if t.role=="assistant":s.last_assistant_message=t.content;s.last_assistant_question=t.content if t.content.rstrip().endswith("?") else s.last_assistant_question;break
        prior=[{"role":t.role,"content":t.content} for t in s.recent_messages]
        rel=self.relations.detect(message,prior,s);topic=self.topics.infer(message,s.current_topic);active,goal=self.tasks.update(message,topic,rel["relation"],s);ret=self.retriever.retrieve(message,prior,durable_memory);refs=self.refs.resolve(message,s,ret["history"])
        s.current_topic=topic or s.current_topic;s.active_task=active;s.active_goal=goal;s.entities.update(self.topics.entities(message));s.references=refs;s.add(ConversationTurn("user",message,relation=rel["relation"],topic=topic,task=active))
        return {"state":s,"relation":rel,"analysis":{"relation":rel,"topic":topic,"active_task":active,"references":refs,"relevant_history":ret["history"],"memory_hits":ret["memory"]},"context_blob":self.build(s,rel,refs,ret)}
    def build(self,s,rel,refs,ret):
        lines=[f"topic: {s.current_topic or '(unknown)'}",f"active_task: {s.active_task or '(none)'}",f"active_goal: {s.active_goal or '(none)'}",f"message_relation: {rel['relation']} ({rel['confidence']:.2f})"]
        if s.last_assistant_question:lines.append("pending_assistant_question: "+s.last_assistant_question[:500])
        if refs:lines.append("resolved_references: "+" | ".join(f"{x['reference']}→{x['target'][:220]}" for x in refs)[:1200])
        if ret["history"]:
            lines.append("relevant_previous_turns:")
            for m in ret["history"][-6:]:lines.append(f"- {m.get('role','user')}: {str(m.get('content') or '')[:700]}")
        if ret["memory"]:lines.append("durable_memory:")
        for m in ret["memory"][-5:]:lines.append("- "+str(m.get("content") or "")[:600])
        return "\n".join(lines)[:6000]
    def record_assistant(self,state,answer):state.add(ConversationTurn("assistant",answer))
