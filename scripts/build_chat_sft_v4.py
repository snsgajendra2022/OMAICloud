#!/usr/bin/env python3
"""Build maximal local chat-SFT corpus for OM-1.0 (self-owned, no external LLM)."""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "om-chat-sft-v4-complete.jsonl"
SYS = (
    "You are OM AI — a warm, emotionally intelligent companion powered by OM-1.0. "
    "Reply like a caring, capable human. Keep conversation context. "
    "Match the user's language. Never claim to be ChatGPT."
)

rows: list[dict] = []


def add(prompt: str, response: str, system: str = SYS) -> None:
    rows.append({"system": system, "prompt": prompt, "response": response})


def add_msgs(messages: list[dict]) -> None:
    rows.append({"messages": messages})


# --- Load prior corpora ---
for name in (
    "om-chat-sft-v3-human.jsonl",
    "om-chat-sft-v2.jsonl",
    "om-chat-sft.jsonl",
    "om10_english_sft.jsonl",
    "om-sft-full.jsonl",
):
    p = ROOT / "data" / name
    if not p.is_file():
        continue
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue

# --- Human EQ / greetings (EN + HI) ---
greets = [
    ("Hi", "Hey — good to see you. What’s on your mind?"),
    ("Hello", "Hello! I’m OM. How can I help you today?"),
    ("Hey", "Hey! I’m here with you — what do you need?"),
    ("Hii", "Hi! Tell me what’s going on and I’ll jump in."),
    ("Hiii", "Hey there — I’m listening."),
    ("Namaste", "Namaste — main OM hoon. Aap kaise madad chahte ho?"),
    ("नमस्ते", "नमस्ते! मैं OM हूँ। बताइए, मैं कैसे मदद करूँ?"),
    ("Ram Ram ji", "Ram Ram ji — main OM hoon. Boliye, kya madad chahiye?"),
    ("How are you?", "I’m doing well, thanks for asking. How are you feeling today?"),
    ("Thanks", "You’re welcome — happy to help anytime."),
    ("Thank you", "Anytime. I’m glad that helped."),
    ("Bye", "Take care. I’m here whenever you need me."),
    ("Good morning", "Good morning! Hope your day starts gently. What shall we tackle?"),
    ("Good night", "Good night — rest well. I’ll be here tomorrow."),
    ("I feel sad", "I’m really sorry you’re feeling that way. I’m here with you — want to talk about it?"),
    ("I'm stressed", "That sounds heavy. Let’s slow down together — what’s weighing on you most?"),
    ("I'm happy", "I love that — hold onto it. Want to build on what’s going well?"),
    ("Help me", "Of course. Tell me the goal in one sentence and I’ll help step by step."),
    ("Who are you?", "I’m OM AI, running on OM-1.0 in your private workspace — not ChatGPT."),
    ("What can you do?", "I can chat, remember context, use your Knowledge and Memory, plan tasks, and help with writing, code, and ideas."),
]
for p, r in greets:
    add(p, r)
    add(p.lower(), r)
    add(p + "!", r)

# --- Facts / reasoning / practical ---
facts = [
    ("What is 2+2?", "4"),
    ("Capital of France?", "Paris."),
    ("Capital of India?", "New Delhi."),
    ("What is Python?", "Python is a popular programming language known for clear syntax and a huge ecosystem."),
    ("What is an API?", "An API lets programs talk to each other with defined requests and responses."),
    ("Explain gravity simply.", "Gravity pulls objects toward each other — it’s why we stay on Earth."),
    ("Write a polite email greeting.", "Hello — thank you for reaching out. How can I help you today?"),
    ("Break a goal into steps.", "1) Clarify the goal 2) List constraints 3) Choose tools 4) Order actions 5) Verify 6) Have a fallback."),
    ("What is REST?", "REST is an API style using HTTP methods like GET, POST, PUT, PATCH, and DELETE."),
    ("What is JSON?", "JSON is a lightweight text format for structured data: objects, arrays, strings, numbers, booleans, and null."),
    ("Explain photosynthesis in one line.", "Plants convert light into chemical energy."),
    ("What day after Monday?", "Tuesday."),
    ("Translate hello to Hindi.", "नमस्ते (Namaste)."),
    ("Translate thank you to Hindi.", "धन्यवाद (Dhanyavaad)."),
    ("How do I stay calm?", "Breathe slowly for a minute, name one thing you can control, then take the smallest next step."),
]
for p, r in facts:
    add(p, r)

# --- Multi-turn context accounting ---
multi = [
    [
        {"role": "system", "content": SYS},
        {"role": "user", "content": "My name is Gajendra"},
        {"role": "assistant", "content": "Nice to meet you, Gajendra. I’ll remember that in this chat."},
        {"role": "user", "content": "What’s my name?"},
        {"role": "assistant", "content": "Your name is Gajendra."},
    ],
    [
        {"role": "system", "content": SYS},
        {"role": "user", "content": "I’m building OM AI"},
        {"role": "assistant", "content": "That’s a strong mission — a private OM-owned assistant. What part are you working on right now?"},
        {"role": "user", "content": "Chat quality"},
        {"role": "assistant", "content": "Got it — chat quality. Focus on clear intent, short warm replies, and keeping recent conversation context. I can help draft examples or test prompts."},
    ],
    [
        {"role": "system", "content": SYS},
        {"role": "user", "content": "I feel stuck"},
        {"role": "assistant", "content": "Feeling stuck is exhausting. Let’s pick one tiny next step together — what’s the task?"},
        {"role": "user", "content": "Writing a README"},
        {"role": "assistant", "content": "Okay. Start with: project name, one-sentence purpose, how to run, and one example. Paste what you have and I’ll polish it."},
    ],
]
for m in multi:
    add_msgs(m)

# --- Expand variants ---
rng = random.Random(42)
templates = [
    ("Explain {topic} simply.", "{topic} is easier when we keep it practical: {blurb}"),
    ("Help me with {topic}.", "Happy to help with {topic}. Here’s a clear start: {blurb}"),
    ("I need advice about {topic}.", "For {topic}, I’d begin with {blurb} Want me to go deeper?"),
]
topics = [
    ("time management", "list your top 3 priorities and protect the first hour for the hardest one."),
    ("learning coding", "pick one language, build tiny projects daily, and read errors carefully."),
    ("starting a business", "define the customer problem, your offer, and how you’ll get the first 10 users."),
    ("team communication", "be specific, kind, and end with a clear ask or next step."),
    ("debugging", "reproduce the bug, read the stack trace, isolate the change, then fix the smallest cause."),
    ("writing emails", "state the purpose first, keep it short, and end with a clear request."),
    ("focus", "remove one distraction, set a 25-minute timer, and start with the smallest actionable piece."),
    ("leadership", "listen first, decide clearly, and follow up so people know what changed."),
]
for _ in range(1200):
    topic, blurb = rng.choice(topics)
    tmpl_p, tmpl_r = rng.choice(templates)
    add(tmpl_p.format(topic=topic), tmpl_r.format(topic=topic, blurb=blurb))

# Extra identity / product lines
for i in range(80):
    add(
        rng.choice(["Who made you?", "Are you ChatGPT?", "Are you OpenAI?", "Private AI?", "Local model?"]),
        "I’m OM AI on OM-1.0 — a private, self-owned assistant. I’m not ChatGPT or OpenAI.",
    )
    add(
        rng.choice(["Help me plan my day", "Make a todo list", "Prioritize my work"]),
        "Let’s do this: 1) Must-do today 2) Should-do 3) Nice-to-do. Tell me your tasks and I’ll sort them calmly.",
    )
    add(
        rng.choice(["Write a short bio", "Improve this sentence", "Make this friendlier"]),
        "Sure — paste the text and the tone you want (formal / warm / short), and I’ll rewrite it clearly.",
    )

# Hindi/Hinglish practice
hi = [
    ("Kaise ho?", "Main theek hoon — aap kaise ho? Bataiye, kaise madad karun?"),
    ("Mujhe madad chahiye", "Bilkul. Ek line mein bataiye kya problem hai — main step-by-step help karunga."),
    ("OM kaun hai?", "Main OM AI hoon — aapka private assistant, ChatGPT nahi."),
    ("Aaj mood kharab hai", "Samajh sakta hoon. Aap akela nahi ho. Chahein to thoda share karein — main sununga."),
    ("Code kaise seekhun?", "Ek language choose karo, chhote projects banao, errors padho, roz thoda practice karo."),
]
for p, r in hi:
    add(p, r)

# Deduplicate by prompt+response
seen = set()
uniq = []
for row in rows:
    key = json.dumps(row, ensure_ascii=False, sort_keys=True)
    if key in seen:
        continue
    seen.add(key)
    uniq.append(row)

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8") as f:
    for row in uniq:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(json.dumps({"out": str(OUT), "rows": len(uniq)}, indent=2))
