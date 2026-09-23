"""Layer registry — architecture names → real package paths."""
from __future__ import annotations

from typing import Any

# Final OM Companion architecture (13 layers + runtime)
ARCHITECTURE_LAYERS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Human Understanding",
        "path": "om_ai/core/human_intelligence/",
        "modules": [
            "human_meaning_engine",
            "intent_understanding",
            "context_engine",
            "implicit_meaning",
            "conversation_feeling",
            "user_state",
            "human_context_engine",
            "human_conversation_pipeline",
        ],
        "role": "what / why / intent / missing info / situation",
    },
    {
        "id": 2,
        "name": "Emotion & Empathy",
        "path": "om_ai/core/emotion_intelligence/",
        "modules": [
            "emotion_detector",
            "emotion_engine",
            "empathy_engine",
            "tone_controller",
            "mood_tracker",
            "emotional_memory",
        ],
        "role": "detect affect → tone + response style",
    },
    {
        "id": 3,
        "name": "Memory",
        "path": "om_ai/core/memory/ + companion_memory + human_memory",
        "modules": [
            "short_term_memory",
            "long_term_memory",
            "memory_retriever",
            "preference_memory",
            "conversation_memory",
        ],
        "role": "name, preferences, projects, style, events",
    },
    {
        "id": 4,
        "name": "Conversation Intelligence",
        "path": "om_ai/core/dialogue_intelligence/",
        "modules": [
            "dialogue_manager",
            "turn_manager",
            "followup_engine",
            "question_engine",
            "interruption_manager",
        ],
        "role": "answer / ask / explain / listen / wait / encourage",
    },
    {
        "id": 5,
        "name": "Reasoning",
        "path": "om_ai/core/reasoning/ + chat_intelligence",
        "modules": [
            "reasoning_engine",
            "hypothesis_engine",
            "problem_analyzer",
            "planning_engine",
            "verification_engine",
        ],
        "role": "analyze → possibilities → evidence → solution → verify",
    },
    {
        "id": 6,
        "name": "Knowledge Intelligence",
        "path": "om_ai/core/knowledge/ → om_ai/knowledge/",
        "modules": [
            "document_loader",
            "embedding_engine",
            "vector_database",
            "knowledge_graph",
            "retrieval_engine",
        ],
        "role": "docs → embeddings → vector search → relevant knowledge (NOT 100M prompt dump)",
    },
    {
        "id": 7,
        "name": "Research Engine",
        "path": "om_ai/core/deep_research/ + companion_runtime/search_care",
        "modules": [
            "research_router",
            "search_agent",
            "source_ranker",
            "evidence_engine",
            "search_care",
        ],
        "role": "search → collect → verify → summarize; open browser ONLY on go/open/kholo",
    },
    {
        "id": 8,
        "name": "Action + Permission",
        "path": "om_ai/core/action_control/",
        "modules": [
            "action_planner",
            "permission_engine",
            "tool_executor",
            "security_policy",
        ],
        "role": "plan → ask permission → execute → verify",
    },
    {
        "id": 9,
        "name": "Personality",
        "path": "om_ai/core/personality/ + companion_personality + human_companion/personality",
        "modules": [
            "identity",
            "communication_style",
            "humor_engine",
            "relationship_engine",
        ],
        "role": "brother/bhai — warmth, consistency, human voice (not robot)",
    },
    {
        "id": 10,
        "name": "Voice Intelligence",
        "path": "om_ai/core/voice/ → voice_intelligence + audio_intelligence",
        "modules": [
            "voice_activity_detector",
            "streaming_stt",
            "streaming_tts",
            "interruption_detector",
        ],
        "role": "STT → partial understand → think → stream TTS",
    },
    {
        "id": 11,
        "name": "Avatar / Presence",
        "path": "om_ai/core/avatar/ → presence_engine + human_companion/avatar",
        "modules": [
            "avatar_state",
            "expression_engine",
            "lip_sync",
            "gesture_engine",
        ],
        "role": "listening / thinking / speaking presence",
    },
    {
        "id": 12,
        "name": "Self Improvement",
        "path": "om_ai/core/self_learning/ → self_improvement",
        "modules": [
            "feedback_engine",
            "failure_detector",
            "evaluation_engine",
            "improvement_memory",
        ],
        "role": "learn from wrong answers, corrections, failed actions",
    },
    {
        "id": 13,
        "name": "Final OM Runtime",
        "path": "om_ai/core/companion_runtime/ + companion_architecture",
        "modules": ["companion_runtime", "companion_pipeline"],
        "role": "voice → understand → memory → reason → permission → action → verify → human reply → voice",
    },
]


def layer_status() -> list[dict[str, Any]]:
    """Probe imports for each layer (honest status)."""
    import importlib

    probes = {
        1: "om_ai.core.human_intelligence",
        2: "om_ai.core.emotion_intelligence",
        3: "om_ai.core.memory",
        4: "om_ai.core.dialogue_intelligence",
        5: "om_ai.core.reasoning",
        6: "om_ai.core.knowledge",
        7: "om_ai.core.deep_research",
        8: "om_ai.core.action_control",
        9: "om_ai.core.personality",
        10: "om_ai.core.voice",
        11: "om_ai.core.avatar",
        12: "om_ai.core.self_learning",
        13: "om_ai.core.companion_architecture",
    }
    out: list[dict[str, Any]] = []
    for layer in ARCHITECTURE_LAYERS:
        lid = int(layer["id"])
        mod = probes.get(lid, "")
        ok = False
        err = ""
        try:
            importlib.import_module(mod)
            ok = True
        except Exception as exc:
            err = str(exc)[:120]
        out.append(
            {
                "id": lid,
                "name": layer["name"],
                "status": "ok" if ok else "missing",
                "import": mod,
                "error": err,
            }
        )
    return out
