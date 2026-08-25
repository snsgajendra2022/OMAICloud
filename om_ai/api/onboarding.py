"""First-login workspace bootstrap — defaults for every new OM user."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

WELCOME_TITLE = "Welcome to OM"
WELCOME_ASSISTANT = (
    "Hi — I’m OM. I’m here with you, not just answering questions.\n\n"
    "Tell me what’s on your mind: work, feelings, a plan, a bug, or just a hello. "
    "I’ll listen carefully, keep our conversation in mind, and reply like a real teammate.\n\n"
    "Tip: open Library, Assistants, Knowledge, and Memory from the sidebar — "
    "I already set up a few starters for you."
)

DEFAULT_ASSISTANT_PROMPT = (
    "You are OM Companion — warm, emotionally intelligent, and practical.\n"
    "Listen first. Mirror the user's feelings briefly when it helps, then give a clear useful answer.\n"
    "Remember conversation context. Prefer short natural sentences over stiff essays.\n"
    "Match the user's language (English, Hindi, Hinglish, etc.). Never claim to be ChatGPT."
)

DEFAULT_PROMPTS = [
    (
        "Warm reply",
        "Reply with empathy and clarity. Acknowledge feelings, then help with the next step:\n\n",
    ),
    (
        "Explain simply",
        "Explain this in simple, friendly language without jargon:\n\n",
    ),
    (
        "Action plan",
        "Turn this into a calm, ordered action plan with 3–7 steps:\n\n",
    ),
    (
        "Email draft",
        "Draft a polite, human email for this situation:\n\n",
    ),
]

DEFAULT_LIBRARY = [
    (
        "Getting started with OM",
        "document",
        "OM is your private AI workspace.\n\n"
        "• Chat — talk naturally; OM keeps recent context\n"
        "• Library — save useful answers and notes\n"
        "• Assistants — specialized helpers with their own instructions\n"
        "• Knowledge — documents OM can search\n"
        "• Memory — facts you want OM to remember\n"
        "• Prompts — reusable starters\n\n"
        "You own the model path: no OpenAI/Anthropic as the core brain.",
    ),
    (
        "How OM replies best",
        "snippet",
        "For better answers:\n"
        "1) Share a little context (who / what / why)\n"
        "2) Say how you feel if it matters (stressed, curious, stuck)\n"
        "3) Ask for the format you want (short, steps, email, code)\n",
    ),
]

KNOWLEDGE_TIP = (
    "OM keeps chats, library, memory, and knowledge private to your account. "
    "Use Assistants for specialized roles. Use Scheduled for recurring reminders. "
    "Speak naturally — OM tries to understand messy spelling and intent."
)


def bootstrap_user_workspace(
    tenant_id: str,
    actor: str,
    *,
    display_name: str = "",
) -> dict[str, Any]:
    """Idempotent: create sensible defaults if this user has an empty workspace."""
    created: dict[str, Any] = {
        "workspace": False,
        "welcome_chat": False,
        "assistant": False,
        "library": 0,
        "prompts": 0,
        "memory": False,
        "knowledge": False,
        "scheduled": False,
        "notification": False,
    }
    name = (display_name or "there").strip() or "there"
    tenant_id = tenant_id or "default"
    actor = actor or "anonymous"

    try:
        from om_ai.api.conversations import get_store as get_conv_store
        from om_ai.api.platform_store import get_platform_store
        from om_ai.api.workspace_store import get_workspace_store
    except Exception as exc:
        logger.warning("onboarding imports failed: %s", exc)
        return {"ok": False, "error": str(exc), "created": created}

    try:
        pstore = get_platform_store()

        spaces = pstore.list_workspaces(tenant_id, actor)
        if not spaces:
            pstore.create_workspace(tenant_id, actor, name=f"{name}'s workspace")
            created["workspace"] = True

        lib = pstore.list_library(tenant_id, actor)
        if not lib:
            for title, kind, content in DEFAULT_LIBRARY:
                pstore.create_library_item(
                    tenant_id, actor, title=title, content=content, kind=kind
                )
                created["library"] += 1

        prompts = pstore.list_prompts(tenant_id, actor)
        if not prompts:
            for pname, content in DEFAULT_PROMPTS:
                pstore.create_prompt(tenant_id, actor, name=pname, content=content)
                created["prompts"] += 1

        memories = pstore.list_memories(tenant_id, actor)
        if not memories:
            pstore.create_memory(
                tenant_id,
                actor,
                content=(
                    f"User prefers warm, human replies. Display name: {name}. "
                    "Match their language and remember recent chat context."
                ),
                importance=0.8,
            )
            created["memory"] = True

        sources = pstore.list_knowledge_sources(tenant_id, actor)
        if not sources:
            # Store tip text as a file + knowledge source metadata
            pstore.create_file(
                tenant_id,
                actor,
                name="om-getting-started.txt",
                content_text=KNOWLEDGE_TIP,
                mime="text/plain",
            )
            pstore.create_knowledge_source(
                tenant_id,
                actor,
                name="OM workspace tips",
                source_type="document",
                uri="om://tips/getting-started",
                doc_count=1,
                status="stored",
            )
            try:
                from om_ai.api import main as app_main
                import uuid as _uuid

                app_main.knowledge.add(
                    _uuid.uuid4().hex,
                    KNOWLEDGE_TIP,
                    {"source": "OM workspace tips", "actor": actor},
                    tenant_id=tenant_id,
                )
            except Exception:
                pass
            created["knowledge"] = True

        tasks = pstore.list_tasks(tenant_id, actor)
        scheduled = [
            t for t in tasks if (t.get("kind") or "") == "scheduled" or t.get("schedule")
        ]
        if not scheduled:
            pstore.create_scheduled_task(
                tenant_id,
                actor,
                title="Weekly reflection with OM",
                schedule="weekly",
                payload={
                    "prompt": "Help me review my week kindly and suggest 3 priorities.",
                    "paused_hint": True,
                },
            )
            # Pause so it does not auto-run until the user enables it
            created_task = [
                t
                for t in pstore.list_tasks(tenant_id, actor)
                if t.get("title") == "Weekly reflection with OM"
            ]
            if created_task:
                try:
                    pstore.update_task(
                        created_task[0]["id"],
                        tenant_id,
                        actor,
                        status="paused",
                    )
                except Exception:
                    pass
            created["scheduled"] = True

        wstore = get_workspace_store()
        assistants = wstore.list_assistants(tenant_id, actor)
        if not assistants:
            wstore.create_assistant(
                tenant_id,
                actor,
                name="OM Companion",
                description="Warm default assistant — empathy + clear help.",
                system_prompt=DEFAULT_ASSISTANT_PROMPT,
                model="OM-1.0",
            )
            created["assistant"] = True

        cstore = get_conv_store()
        convs = cstore.list_conversations(tenant_id, actor)
        if not convs:
            conv = cstore.create_conversation(tenant_id, actor, title=WELCOME_TITLE)
            cstore.append_messages(
                conv.id,
                tenant_id,
                actor,
                [{"role": "assistant", "content": WELCOME_ASSISTANT}],
                auto_title=False,
            )
            cstore.set_last_conversation(tenant_id, actor, conv.id)
            created["welcome_chat"] = True
            created["conversation_id"] = conv.id

        notes = pstore.list_notifications(tenant_id, actor)
        if not notes:
            pstore.create_notification(
                tenant_id,
                actor,
                title="Your OM workspace is ready",
                body=(
                    "Defaults are set: Welcome chat, Companion assistant, "
                    "Library, Prompts, Knowledge, Scheduled, and Memory."
                ),
            )
            created["notification"] = True

        return {"ok": True, "created": created}
    except Exception as exc:
        logger.exception("workspace bootstrap failed")
        return {"ok": False, "error": str(exc), "created": created}
