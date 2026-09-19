"""STEP 100 — Central consciousness: Input → Understand → Decide → Plan → Act → Learn."""
from __future__ import annotations

import logging
from typing import Any

from .attention_manager import AttentionManager
from .awareness_manager import AwarenessManager
from .decision_engine import DecisionEngine
from .goal_understanding import GoalUnderstanding
from .intention_engine import IntentionEngine
from .self_state import SelfState
from .thought_manager import ThoughtManager

logger = logging.getLogger(__name__)
_ENGINE: ConsciousnessEngine | None = None


class ConsciousnessEngine:
    def __init__(self) -> None:
        self.state = SelfState()
        self.awareness = AwarenessManager()
        self.attention = AttentionManager()
        self.intention = IntentionEngine()
        self.goals = GoalUnderstanding()
        self.thoughts = ThoughtManager()
        self.decisions = DecisionEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "step": 100,
            "name": "OM Consciousness Runtime",
            "state": self.state.to_dict(),
        }

    def boot_greeting(self) -> str:
        name = self.state.user_name or "Sir"
        self.state.mode = "listening"
        return f"Good morning {name}. I am ready."

    def process(
        self,
        text: str,
        *,
        answer: str = "",
        memory_blob: str = "",
        affect: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Full conscious turn. Emits activity stream for live presence."""
        self.state.mode = "thinking"
        self.state.activity = []
        out: dict[str, Any] = {"step": 100}

        # Emit live events if bus available
        bus = None
        try:
            from om_ai.core.live_presence import get_event_bus
            bus = get_event_bus()
        except Exception:
            bus = None

        def emit(label: str, stage: str = "activity") -> None:
            self.state.activity.append(label)
            if bus:
                try:
                    bus.emit(stage, {"label": label, "text": text[:120]})
                except Exception:
                    pass

        emit("Voice activated")
        mem = memory_blob
        if not mem:
            try:
                from om_ai.core.human_memory import get_human_memory
                mem = get_human_memory().recall_blob()
            except Exception:
                mem = ""

        aware = self.awareness.scan(text, memory_blob=mem)
        out["awareness"] = aware
        emit("Understanding request")
        if aware.get("has_memory"):
            emit("Checking memory")

        attn = self.attention.focus(aware)
        out["attention"] = attn
        intent = self.intention.infer(text, attn)
        out["intention"] = intent
        goal = self.goals.parse(intent, text)
        out["goal"] = goal
        self.state.last_goal = str(goal.get("goal") or "")
        self.state.focus = str(intent.get("intent") or "")

        thought_list = self.thoughts.think(goal, aware)
        out["thoughts"] = thought_list
        for t in thought_list[2:]:
            emit(str(t.get("label") or "Thinking"))

        decision = self.decisions.decide(goal)
        out["decision"] = decision
        emit(f"Routing → {decision.get('route')}")

        # Act via route
        reply = answer
        route = decision.get("route")
        try:
            if route == "action_engine" or decision.get("plan_first"):
                from om_ai.core.action_engine import get_action_engine
                plan = get_action_engine().plan(text)
                out["action"] = plan
                reply = str(plan.get("spoken") or reply)
                emit("Analysis plan ready")
            elif route == "human_dialogue" or route == "brain":
                # Annotate dialogue/emotion only — conversation content comes from the brain
                try:
                    from om_ai.core.human_dialogue import get_human_dialogue
                    out["dialogue"] = get_human_dialogue().respond(text)
                except Exception:
                    pass
                # Keep incoming answer from companion brain / OS
                reply = answer or reply
            elif route == "personality":
                # Greeting / tone stays with companion brain — no canned personality.greet
                pass
            elif route == "vision":
                from om_ai.core.vision import get_vision_runtime
                vision = get_vision_runtime().what_is_on_screen()
                out["vision"] = vision
                reply = (
                    "I cannot access the screen yet without permission, Sir. "
                    "Enable screen vision and I will describe what you are looking at."
                )
            elif route == "language_intelligence":
                from om_ai.core.language_intelligence import get_language_intelligence
                lang = get_language_intelligence().understand(text)
                out["language"] = lang
                # leave reply for companion OS language handler if empty
        except Exception as exc:
            logger.debug("consciousness act: %s", exc)
            out["act_error"] = str(exc)

        # Personality polish
        try:
            from om_ai.core.personality import get_personality
            reply = get_personality().style_reply(reply or "", intent=intent.get("intent") or "")
        except Exception:
            pass

        # Learn
        try:
            from om_ai.core.human_memory import get_human_memory
            out["memory"] = get_human_memory().observe_turn(text, reply or "", affect=affect)
            emit("Memory updated")
        except Exception:
            pass

        self.state.mode = "speaking" if reply else "listening"
        out["answer"] = reply or answer
        out["spoken"] = out["answer"]
        out["activity"] = list(self.state.activity[-16:])
        out["self_state"] = self.state.to_dict()
        return out


def get_consciousness() -> ConsciousnessEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = ConsciousnessEngine()
    return _ENGINE
