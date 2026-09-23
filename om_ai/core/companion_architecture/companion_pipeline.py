"""Final OM Companion Pipeline — all 13 architecture layers in one turn.

Flow:
  Voice/Text
    → Human Understanding
    → Emotion & Empathy
    → Memory
    → Conversation Intelligence
    → Reasoning (when needed)
    → Knowledge retrieval (when needed)
    → Research (search without browser unless go/open)
    → Action + Permission
    → Personality (brother)
    → Human Response
    → (caller) Voice + Avatar
    → Self Improvement note
"""
from __future__ import annotations

import re
from typing import Any, Callable

_PIPE: "CompanionPipeline | None" = None


def _locale(text: str) -> str:
    low = (text or "").lower()
    if re.search(
        r"[\u0900-\u097F]|\b(hai|hain|kya|tum|nahi|karo|batao|mujhe|bhai|theek|thak)\b",
        low,
    ):
        return "hi"
    return "en"


class CompanionPipeline:
    """Canonical end-to-end companion turn matching the final architecture."""

    def __init__(self) -> None:
        from om_ai.core.human_intelligence.human_context_engine import HumanContextEngine
        from om_ai.core.emotion_intelligence import EmotionEngine
        from om_ai.core.dialogue_intelligence import DialogueManager
        from om_ai.core.personality import get_personality
        from om_ai.core.wellbeing_intelligence import WellbeingEngine

        self.context_engine = HumanContextEngine()
        self.emotion_engine = EmotionEngine()
        self.dialogue_manager = DialogueManager()
        self.personality_engine = get_personality()
        self.wellbeing_engine = WellbeingEngine()

    def run(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        memory_blob: str = "",
        profile: dict[str, Any] | None = None,
        locale: str | None = None,
        generate: Callable[..., str] | None = None,
        pre_answer: str = "",
        allow_actions: bool = True,
    ) -> dict[str, Any]:
        hist = history or []
        profile = profile or {}
        loc = locale or _locale(message)
        stages: list[str] = []

        # —— STEP 71 Human Presence (why before what) ——
        try:
            from om_ai.core.human_presence import run_human_presence

            presence = run_human_presence(
                message, history=hist, profile=profile, locale=loc
            )
            stages.append("human_presence")
            if presence.get("block_solution_engine") and presence.get("seed_reply"):
                return {
                    "answer": str(presence["seed_reply"]),
                    "spoken": str(presence["seed_reply"]),
                    "intent": "sharing",
                    "emotion": (presence.get("emotion") or {}).get("emotion"),
                    "need": "conversation",
                    "response_style": "supportive",
                    "tone": "warm",
                    "listen_first": True,
                    "human_presence": presence,
                    "stages": stages + ["presence_listen"],
                    "pipeline": stages + ["presence_listen"],
                    "architecture": "companion_v1_step71",
                    "bond": "brother",
                    "avatar_state": presence.get("avatar_state") or "listening",
                }
            if presence.get("requires_permission") and presence.get("permission_prompt"):
                return {
                    "answer": str(presence["permission_prompt"]),
                    "spoken": str(presence["permission_prompt"]),
                    "intent": "action",
                    "action_plan": {
                        "requires_permission": True,
                        "speak": presence["permission_prompt"],
                    },
                    "human_presence": presence,
                    "stages": stages + ["presence_permission"],
                    "architecture": "companion_v1_step71",
                    "bond": "brother",
                    "avatar_state": "thinking",
                }
        except Exception:
            pass

        # —— 1. Human Understanding ——
        emo_seed = self.emotion_engine.analyze(message, history=hist)
        human = self.context_engine.understand(message, history=hist, emotion=emo_seed)
        stages.append("human_understanding")

        # —— 2. Emotion & Empathy ——
        wellbeing = self.wellbeing_engine.observe(message, locale=loc)
        emo = self.emotion_engine.analyze(
            message,
            history=hist,
            listen_first_hint=bool(human.get("listen_first") or wellbeing.get("active")),
        )
        if wellbeing.get("active"):
            emo["need"] = "conversation"
            emo["response_style"] = "supportive"
            emo["tone"] = "warm"
            emo["followup_required"] = True
            human["listen_first"] = True
            if wellbeing.get("care_line"):
                human["natural_ask"] = wellbeing["care_line"]
        low = (message or "").lower()
        if re.search(r"(?i)\b(i am|i'?m|feeling)?\s*(very\s+)?tired\b|\bthak\b|\bbad day\b", low):
            emo.update(
                {
                    "emotion": emo.get("emotion") if emo.get("emotion") not in {"neutral"} else "fatigue",
                    "label": "fatigue" if "tired" in low or "thak" in low else (emo.get("label") or "sad"),
                    "need": "conversation",
                    "response_style": "supportive",
                    "tone": "warm",
                    "followup_required": True,
                }
            )
            human["listen_first"] = True
            if not human.get("natural_ask"):
                human["natural_ask"] = (
                    "Bhai, aaj thakaan sunai de rahi hai. Busy din tha, ya kuch aur dil pe hai?"
                    if loc == "hi"
                    else "You sound tired today. Was it a busy day, or is something bothering you?"
                )
        stages.append("emotion_empathy")

        # —— 3. Memory ——
        recall_extra = ""
        try:
            from om_ai.core.companion_runtime.search_care import recall_search_context

            recall_extra = recall_search_context(message)
        except Exception:
            pass
        memory = {
            "blob": (memory_blob or "")[:2000],
            "profile": profile,
            "who": str(profile.get("name") or "bhai"),
            "preferences": profile.get("preferences") or {},
            "search_notes": recall_extra[:1500],
            "dialogue": self.context_engine.memory.to_dict(),
        }
        stages.append("memory")

        # —— 7 early: Research intent (search without open) ——
        research_pack: dict[str, Any] = {}
        action_plan: dict[str, Any] | None = None
        try:
            from om_ai.core.companion_runtime.search_care import (
                extract_search_query,
                is_search_request,
                research_query,
                wants_browser_open,
                google_url,
            )

            if is_search_request(message):
                q = extract_search_query(message)
                if wants_browser_open(message):
                    action_plan = {
                        "action": "browser.open",
                        "target": google_url(q),
                        "requires_permission": False,
                        "speak": (
                            f"Theek hai bhai, Google khol raha hun{(' — ' + q) if q else ''}."
                            if loc == "hi"
                            else f"Opening Google for you, brother{(' — ' + q) if q else ''}."
                        ),
                    }
                else:
                    research_pack = research_query(q, user_message=message)
                    stages.append("research")
        except Exception:
            pass

        # —— 8. Action intent (permission first for opens) ——
        if allow_actions and not research_pack and not action_plan:
            action_plan = self._detect_action(message, loc=loc)
            if action_plan:
                stages.append("action_permission")

        # —— 4. Conversation Intelligence ——
        is_action = bool(action_plan) or bool(research_pack)
        dialogue = self.dialogue_manager.plan(
            message,
            human=human,
            emotion=emo,
            is_action=is_action,
            locale=loc,
        )
        stages.append("conversation_intelligence")

        # —— 5–6. Reasoning + Knowledge (when not research/action/listen) ——
        reasoning_pack: dict[str, Any] = {}
        knowledge_pack: dict[str, Any] = {}
        if (
            not research_pack
            and not action_plan
            and not human.get("listen_first")
            and self._needs_reasoning(message)
        ):
            reasoning_pack = self._reason(message)
            stages.append("reasoning")
            knowledge_pack = self._retrieve_knowledge(message)
            if knowledge_pack.get("hits"):
                stages.append("knowledge")

        # —— 9. Personality (brother) ——
        person = self.personality_engine.prepare(
            message,
            emotion=emo,
            human=human,
            profile=profile,
            locale=loc,
        )
        # Force brother bond in hints
        person_hint = str(person.get("system_hint") or "")
        brother_hint = (
            "You are OM — the user's brother (bhai), not a robot or helpdesk. "
            "Feel with them. Care first. Never say 'How can I help you'."
        )
        stages.append("personality")

        system_hint = "\n".join(
            p
            for p in (
                brother_hint,
                str(human.get("system_hint") or ""),
                str(dialogue.get("system_hint") or ""),
                person_hint,
                str(wellbeing.get("system_hint") or "") if wellbeing.get("active") else "",
                f"Memory:\n{memory['blob']}" if memory["blob"] else "",
                memory.get("search_notes") or "",
                str((reasoning_pack or {}).get("hint") or ""),
                str((knowledge_pack or {}).get("hint") or ""),
            )
            if p
        )

        # —— Compose answer ——
        answer = (pre_answer or "").strip()
        if research_pack.get("spoken"):
            answer = str(research_pack["spoken"])
        elif action_plan and action_plan.get("requires_permission"):
            answer = str(action_plan.get("speak") or "")
        elif action_plan and action_plan.get("speak") and action_plan.get("action") == "browser.open":
            answer = str(action_plan["speak"])
        elif not answer and human.get("listen_first") and human.get("natural_ask"):
            answer = str(human["natural_ask"])
        elif not answer and generate:
            try:
                answer = str(generate(message, system_hint) or "").strip()
            except TypeError:
                try:
                    answer = str(generate(message) or "").strip()
                except Exception:
                    answer = ""
            except Exception:
                answer = ""

        if not answer and re.search(r"(?i)^\s*(hey|hi|hello|namaste)\b", message or ""):
            answer = "Haan bhai, main yahan hoon." if loc == "hi" else "Hey brother — I'm right here."

        answer = self._polish(answer, emotion=emo, human=human, locale=loc)
        stages.append("human_response")

        # —— 12. Self improvement note (lightweight) ——
        self._note_turn(message, answer, emo=emo)
        stages.append("self_improvement")

        intent = "action" if action_plan else ("research" if research_pack else "conversation")
        if human.get("listen_first"):
            intent = "sharing"
        elif (human.get("conversation") or {}).get("is_question"):
            intent = "question"

        return {
            "answer": answer,
            "spoken": answer,
            "intent": intent,
            "emotion": emo.get("emotion") or emo.get("label"),
            "need": emo.get("need") or ("conversation" if human.get("listen_first") else "assist"),
            "response_style": emo.get("response_style") or "balanced",
            "tone": emo.get("tone") or "warm",
            "followup_required": bool(emo.get("followup_required") or human.get("listen_first")),
            "listen_first": bool(human.get("listen_first")),
            "human": human,
            "emotion_pack": emo,
            "wellbeing": wellbeing,
            "dialogue": dialogue,
            "memory": memory,
            "personality": person,
            "research": research_pack,
            "reasoning": reasoning_pack,
            "knowledge": knowledge_pack,
            "action_plan": action_plan,
            "system_hint": system_hint,
            "natural_ask": human.get("natural_ask"),
            "stages": stages,
            "pipeline": stages,
            "architecture": "companion_v1_13_layers",
            "bond": "brother",
            "avatar_state": (
                "listening"
                if human.get("listen_first")
                else ("thinking" if reasoning_pack else "speaking")
            ),
        }

    def _detect_action(self, message: str, *, loc: str) -> dict[str, Any] | None:
        low = (message or "").lower()
        # Open project / app — ask permission like architecture example
        m = re.search(
            r"(?i)\b(?:open|kholo|khol)\s+(?:my\s+)?(.+?)(?:\s+please)?$",
            (message or "").strip(),
        )
        if m and not re.search(r"(?i)\b(google|browser|youtube|search)\b", low):
            target = m.group(1).strip(" .")
            if target and len(target) < 80:
                return {
                    "action": "application.open",
                    "target": target,
                    "requires_permission": True,
                    "speak": (
                        f"Bhai, '{target}' mil gaya. Kholun?"
                        if loc == "hi"
                        else f"I found your {target}. Do you want me to open it?"
                    ),
                }
        return None

    def _needs_reasoning(self, message: str) -> bool:
        low = (message or "").lower()
        return bool(
            re.search(
                r"(?i)\b(why|how|fix|error|debug|compare|architecture|design|plan|solve|kaise|kyun)\b",
                low,
            )
        ) and len(low.split()) >= 4

    def _reason(self, message: str) -> dict[str, Any]:
        try:
            from om_ai.core.reasoning.reasoning_engine import ReasoningEngine

            eng = ReasoningEngine()
            if hasattr(eng, "run"):
                out = eng.run(message)
                return {"ok": True, "result": out, "hint": str(out)[:500]}
            if hasattr(eng, "analyze"):
                out = eng.analyze(message)
                return {"ok": True, "result": out, "hint": str(out)[:500]}
        except Exception:
            pass
        try:
            from om_ai.core.chat_intelligence.problem_analyzer import ProblemAnalyzer

            pa = ProblemAnalyzer().analyze(message)
            return {"ok": True, "result": pa, "hint": f"Problem analysis: {pa}"}
        except Exception:
            return {}

    def _retrieve_knowledge(self, message: str) -> dict[str, Any]:
        hits: list[str] = []
        try:
            from om_ai.knowledge.rag import retrieve  # type: ignore

            rows = retrieve(message, limit=3) or []
            for r in rows:
                hits.append(str(getattr(r, "text", None) or r)[:300])
        except Exception:
            try:
                from om_ai.core.knowledge_intelligence.rag_engine import RAGEngine

                pack = RAGEngine().query(message) if hasattr(RAGEngine(), "query") else {}
                if isinstance(pack, dict):
                    for h in list(pack.get("hits") or pack.get("results") or [])[:3]:
                        hits.append(str(h)[:300])
            except Exception:
                pass
        if not hits:
            return {}
        return {
            "hits": hits,
            "hint": "Relevant knowledge:\n" + "\n".join(f"- {h}" for h in hits),
        }

    def _polish(
        self,
        answer: str,
        *,
        emotion: dict[str, Any],
        human: dict[str, Any],
        locale: str,
    ) -> str:
        text = (answer or "").strip()
        for banned in (
            "How can I help you",
            "What can I do for you",
            "Please complete your sentence",
            "As an AI",
            "Share one more detail",
            "How may I assist",
        ):
            if banned.lower() in text.lower():
                text = re.sub(re.escape(banned), "", text, flags=re.I).strip()
        if not text and human.get("natural_ask"):
            text = str(human["natural_ask"])
        if not text and emotion.get("need") in {"conversation", "support_and_listen"}:
            text = (
                "Main sun raha hun bhai — bolo."
                if locale == "hi"
                else "I'm here with you, brother — talk to me."
            )
        return re.sub(r"\s{2,}", " ", text).strip()

    def _note_turn(self, user: str, answer: str, *, emo: dict[str, Any]) -> None:
        try:
            from om_ai.core.self_learning import note_turn

            note_turn(user, answer, emotion=str(emo.get("emotion") or ""))
        except Exception:
            try:
                from om_ai.core.self_improvement.feedback_engine import FeedbackEngine

                fe = FeedbackEngine()
                if hasattr(fe, "observe"):
                    fe.observe(user, answer)
            except Exception:
                pass

    def remember(self, user: str, assistant: str, *, topic: str = "") -> None:
        self.context_engine.remember_turn(user, assistant, topic=topic)


def get_companion_pipeline() -> CompanionPipeline:
    global _PIPE
    if _PIPE is None:
        _PIPE = CompanionPipeline()
    return _PIPE
