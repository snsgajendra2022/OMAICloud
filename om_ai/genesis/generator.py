"""Generate OM-1.0 Genesis-JARVIS SFT instruction JSONL.

This builds *training data*, not a system prompt. Scale with ``--count``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import itertools
from pathlib import Path
from typing import Iterator

from om_ai.genesis.domains import DOMAINS, GENESIS_SYSTEM
from om_ai.genesis.templates import architecture_answer, explain_answer, make_sft_row


def _seed_architectures() -> list[dict]:
    return [
        {
            "domain": "genesis",
            "horizon": "near_future",
            "instruction": "Design the Genesis-JARVIS architecture for OM AI",
            "title": "Genesis-JARVIS Operating Intelligence",
            "understanding": (
                "You need an intelligent operating layer between humans and technology: "
                "cognitive core, agents, digital tools, gated hardware, and a long-term "
                "bio-digital research interface — not a chatbot."
            ),
            "components": [
                "Human interface (text/voice/vision)",
                "OM cognitive core (reason/plan/memory/knowledge)",
                "Agent network (coding/research/security/hardware)",
                "Hardware gateway (IoT/MCU, dry-run default)",
                "Bio-digital research layer (labs only, not production)",
                "Self-improvement loop (feedback → train → deploy)",
            ],
            "data_flow": [
                "Observe",
                "Understand",
                "Think",
                "Plan",
                "Execute",
                "Verify",
                "Improve",
            ],
            "stack": [
                "OM-1.0 owned weights + tokenizer",
                "Memory + RAG",
                "Agents/tools APIs",
                "ESP32/Arduino/RPi contracts (gated)",
                "Eval + continuous learning",
            ],
            "roadmap": [
                "Phase 1: OM AI software foundation",
                "Phase 2: Own model scale 20M→1B→7B→70B",
                "Phase 3: Physical intelligence (sensors/IoT/robotics)",
                "Phase 4: Advanced computing research",
                "Phase 5: Genesis-JARVIS integrated platform",
            ],
            "risks": [
                "Treating research bio-computing as shipped product",
                "Ungated actuator control",
                "Weak memory/tools with a large model only",
                "Disk/compute limits during training",
            ],
            "future": [
                "Neuromorphic accelerators",
                "Spatial/AR interfaces",
                "Controlled bio-electronic research programs",
            ],
            "horizon_note": (
                "Current: software + agents + memory. Near: IoT/robotics. "
                "Long-term: bio-hybrid research — not a complete machine today."
            ),
            "tags": ["genesis", "architecture"],
        },
        {
            "domain": "cognitive_core",
            "horizon": "current",
            "instruction": "Design an AI operating system cognitive core for OM-1.0",
            "title": "OM AI Cognitive Core",
            "understanding": (
                "An AI OS needs reasoning, planning, memory, knowledge retrieval, "
                "tool use, and verification — not text generation alone."
            ),
            "components": [
                "Reasoning engine",
                "Planning engine",
                "Memory engine (short/long/experience)",
                "Knowledge/RAG engine",
                "Tool/action controller",
                "Verifier / critic",
            ],
            "data_flow": [
                "User goal",
                "NLU/intent",
                "Retrieve memory/knowledge",
                "Plan",
                "Tool calls",
                "Verify",
                "Respond",
            ],
            "stack": ["Transformer decoder", "RoPE/RMSNorm/SwiGLU", "Vector RAG", "Agent orchestrator"],
            "roadmap": [
                "Ship tiny owned checkpoint",
                "Strengthen memory + tools",
                "SFT on architecture/coding",
                "Scale parameters with corpus",
            ],
            "risks": ["Hallucinated tool results", "Context overflow", "Unsafe shell/hardware actions"],
            "future": ["Multi-agent debate", "Online learning with gates"],
            "horizon_note": "Current technology — implementable in OM AI now.",
            "tags": ["cognitive_core", "layer-1"],
        },
        {
            "domain": "digital_twin",
            "horizon": "near_future",
            "instruction": "Design a digital twin for a school transport system managed by OM-1.0",
            "title": "School Transport Digital Twin",
            "understanding": (
                "Before changing the real fleet, OM should simulate routes, students, vehicles, "
                "drivers, GPS, and events in a twin."
            ),
            "components": [
                "Route model",
                "Student/vehicle/driver entities",
                "GPS telemetry ingest",
                "Event simulator",
                "OM decision policies",
            ],
            "data_flow": ["Real telemetry", "Twin state", "Simulate scenario", "Recommend", "Gated apply"],
            "stack": ["OM memory/knowledge", "Time-series store", "Map/GPS adapters", "Policy engine"],
            "roadmap": ["Entity schema", "Replay historical GPS", "What-if simulator", "Ops UI"],
            "risks": ["Stale twin state", "Privacy of student data", "Acting without confirmation"],
            "future": ["City-scale multi-fleet twins"],
            "horizon_note": "Near-future engineering — simulate before reality.",
            "tags": ["digital_twin", "layer-7"],
        },
        {
            "domain": "safety",
            "horizon": "current",
            "instruction": "Design the OM-1.0 safety system for tools and hardware actions",
            "title": "OM Safety & Confirmation Layer",
            "understanding": (
                "Every risky action needs validation, least privilege, dry-run defaults, "
                "and clear explanation before physical or destructive digital changes."
            ),
            "components": [
                "Policy engine",
                "Allow-lists",
                "Dry-run mode",
                "Human confirmation gates",
                "Audit log",
            ],
            "data_flow": ["Proposed action", "Policy check", "Simulate/dry-run", "Confirm", "Execute", "Audit"],
            "stack": ["OM /v1/oi gated APIs", "Auth roles", "Action risk tags"],
            "roadmap": ["Tag tool risk", "Confirm UX", "Hardware dry-run", "Incident review"],
            "risks": ["Bypassed gates", "Alert fatigue", "Incomplete audits"],
            "future": ["Formal verification of critical policies"],
            "horizon_note": "Current — must ship with any physical intelligence.",
            "tags": ["safety", "layer-18"],
        },
        {
            "domain": "electronics",
            "horizon": "current",
            "instruction": "Design an OM AI hardware gateway for ESP32 and Raspberry Pi sensors",
            "title": "OM Hardware Gateway",
            "understanding": (
                "Connect the cognitive core to embedded devices safely with auth, "
                "allow-lists, and dry-run defaults."
            ),
            "components": [
                "OI Hardware API",
                "MQTT/serial transports",
                "Device registry",
                "Sensor normalizer",
                "Actuator policy gate",
            ],
            "data_flow": ["Sensor reading", "Ingest API", "Normalize", "Decide", "Gated command"],
            "stack": ["ESP32", "Raspberry Pi", "MQTT", "OM /v1/oi/sensors + /hardware"],
            "roadmap": ["Contracts/stubs", "Dry-run simulator", "Lab devices", "Production allow-list"],
            "risks": ["Accidental actuation", "Untrusted device firmware", "Network spoofing"],
            "future": ["CAN bus industrial cells", "Jetson edge vision nodes"],
            "horizon_note": "Current/near-term engineering — not bio-hybrid.",
            "tags": ["electronics", "layer-9"],
        },
        {
            "domain": "robotics",
            "horizon": "current",
            "instruction": "Create an AI robot architecture controlled by OM-1.0",
            "title": "OM-controlled Robot Stack",
            "understanding": (
                "A useful robot answer needs AI core, perception, control, hardware interface, "
                "learning, and deployment — not a toy description."
            ),
            "components": [
                "AI Core (OM-1.0)",
                "Vision module",
                "Sensor layer",
                "Control layer",
                "Hardware interface",
                "Learning/feedback system",
            ],
            "data_flow": [
                "Environment",
                "Sensors/Camera",
                "Perception",
                "Planner",
                "Controller",
                "Motors",
                "Telemetry → Memory",
            ],
            "stack": ["OM agents", "OpenCV/VLM adapter", "Motor driver MCU", "Safety e-stop"],
            "roadmap": ["Simulate", "Teleop", "Limited autonomy", "Eval safety gates"],
            "risks": ["Unsafe motion", "Sensor failure", "Latency"],
            "future": ["Fleet coordination", "Digital twin of robot cell"],
            "horizon_note": "Current robotics engineering with simulation first.",
            "tags": ["robotics", "layer-10"],
        },
        {
            "domain": "software",
            "horizon": "current",
            "instruction": "Design a production FastAPI + React system for OM AI workspace",
            "title": "OM Workspace Application Architecture",
            "understanding": "Need auth, chat, memory, knowledge, agents, and settings with clear APIs.",
            "components": ["API gateway", "Auth", "Chat/SSE", "Memory DB", "RAG store", "UI"],
            "data_flow": ["Browser", "API", "Orchestrator", "Model/Tools", "Persist", "Stream UI"],
            "stack": ["FastAPI", "SQLite/Postgres", "React chat UI", "OM native model"],
            "roadmap": ["MVP chat", "Memory/RAG", "Agents", "Hardening"],
            "risks": ["Auth gaps", "PII in logs", "Unbounded tool calls"],
            "future": ["Multi-tenant scale-out", "Edge deploy"],
            "horizon_note": "Current software engineering.",
            "tags": ["software", "layer-4"],
        },
        {
            "domain": "bio_digital",
            "horizon": "research",
            "instruction": "Explain the microbial neural mesh concept for Genesis research",
            "title": "Microbial Neural Mesh (Research Concept)",
            "understanding": (
                "This is a long-term bio-electronic research idea using electroactive microbes "
                "and electron transfer patterns — not a product OM can ship today."
            ),
            "components": [
                "Electroactive microbial community (research)",
                "Electron transfer observation",
                "Signal acquisition electronics",
                "AI interpretation layer",
            ],
            "data_flow": [
                "Biological activity",
                "Electron/signal patterns",
                "Instrumentation",
                "Feature extraction",
                "OM AI interpretation",
            ],
            "stack": ["Lab instrumentation", "Microfluidics (research)", "OM analysis notebooks"],
            "roadmap": [
                "Literature + safety framework",
                "Instrumentation prototypes",
                "Signal datasets",
                "Optional model fine-tunes on labeled lab data",
            ],
            "risks": ["Biosafety", "Overclaiming readiness", "Irreproducible wet-lab results"],
            "future": ["Tight bio-electronic co-design under regulated programs"],
            "horizon_note": (
                "LONG-TERM RESEARCH ONLY. Do not present as current OM production technology."
            ),
            "tags": ["research", "bio_digital", "layer-12"],
        },
    ]


def _topic_explains() -> list[dict]:
    rows = []
    explainers = {
        "cognitive_core": [
            (
                "Explain transformer attention for OM-1.0 engineers",
                "Self-attention lets each token weigh others in the sequence. "
                "Multi-head attention learns different relation patterns. "
                "OM uses causal decoder attention with RoPE for positions.",
            ),
            (
                "Explain RAG vs fine-tuning for OM knowledge",
                "RAG retrieves fresh/private docs at inference. Fine-tuning changes weights for style/skills. "
                "Use RAG for company docs; use SFT for stable architect behavior.",
            ),
        ],
        "autonomous_coding": [
            (
                "Design a multi-agent coding workflow for OM",
                "Planner proposes steps; coding agent edits; test agent runs checks; review agent critiques; "
                "master merges only after verify.",
            ),
        ],
        "software": [
            (
                "How should OM design secure APIs?",
                "AuthN/AuthZ on every route, least privilege keys, input validation, rate limits, "
                "no secrets in logs, and dry-run for dangerous tools.",
            ),
            (
                "Explain system design for OM memory service",
                "Separate short-term chat context from long-term preference/project stores; "
                "index knowledge chunks; audit writes; tenant isolation.",
            ),
        ],
        "electronics": [
            (
                "Compare ESP32 vs Raspberry Pi for OM IoT nodes",
                "ESP32: low-power WiFi/BLE sensing/actuation. Raspberry Pi: heavier compute/vision edge. "
                "Gateway policy stays in OM core.",
            ),
            (
                "Explain MQTT role in OM hardware gateway",
                "MQTT publishes sensor telemetry and receives commanded topics. "
                "OM subscribes, validates, and only publishes actuator topics when policy allows.",
            ),
        ],
        "robotics": [
            (
                "Explain motion planning vs low-level motor control",
                "Planning chooses collision-free trajectories; motor control tracks torque/speed setpoints. "
                "OM should own high-level goals; MCU owns tight loops.",
            ),
        ],
        "bio_digital": [
            (
                "What is neuromorphic computing in OM research terms?",
                "Hardware/algorithms inspired by spiking neural efficiency. Useful research direction for "
                "low-power edge cognition — complementary to GPU transformers, not a replacement yet.",
            ),
            (
                "How should OM talk about bio-electronic interfaces?",
                "As research: biological or organic layers + electronic readout + AI interpretation. "
                "Require biosafety/ethics. Never claim production readiness without evidence.",
            ),
        ],
        "microbial_computing": [
            (
                "Explain microbial computing as Genesis research only",
                "Electroactive biological systems + electronic interfaces + signal analysis + AI learning. "
                "Study electron transfer and adaptive networks in labs — not a shipped OM product.",
            ),
        ],
        "digital_twin": [
            (
                "Why simulate before changing a real system?",
                "A twin lets OM test routes, loads, and failure modes without harming users or machines. "
                "Only gated, confirmed actions should affect reality.",
            ),
        ],
        "safety": [
            (
                "What must OM confirm before hardware actuation?",
                "Device identity, allow-list, dry-run result, user/ops approval, and an audit record. "
                "Default deny when unsure.",
            ),
        ],
        "self_improvement": [
            (
                "Describe OM continuous improvement loop",
                "Observe outcomes, measure with evals, learn via datasets/SFT/DPO, optimize, update "
                "only after gates pass.",
            ),
        ],
        "response_intelligence": [
            (
                "Rewrite a flat answer into Genesis response structure",
                "Use Understanding, Analysis, Architecture, Implementation, Validation, Next Steps. "
                "Keep calm, precise, and horizon-honest.",
            ),
        ],
        "genesis": [
            (
                "What is the Observe-Understand-Plan-Execute-Verify-Improve cycle?",
                "OM's mandatory task loop: sense context, parse intent, deliberate, act with tools, "
                "check outcomes, and feed lessons into memory/training.",
            ),
            (
                "How does OM separate current vs research claims?",
                "Label each recommendation: current (ship), near-future (engineer next), "
                "long-term research (lab only). Genesis bio layers are research until proven.",
            ),
        ],
    }
    horizons = {d.id: d.horizon for d in DOMAINS}
    for domain, pairs in explainers.items():
        for instr, body in pairs:
            rows.append(
                {
                    "domain": domain,
                    "horizon": horizons.get(domain, "current"),
                    "instruction": instr,
                    "body": body,
                    "tags": [domain, "explain"],
                }
            )
    return rows


_VARIANTS = [
    "Keep the answer production-minded.",
    "Emphasize safety and gating.",
    "Include a minimal MVP path.",
    "Call out what is research-only.",
    "Map components to OM AI folders/modules.",
]


def iter_examples(*, count: int) -> Iterator[dict]:
    """Yield unique-ish SFT rows up to ``count`` via seeds + variants."""
    seen: set[str] = set()
    produced = 0

    def emit(row: dict) -> dict | None:
        nonlocal produced
        if produced >= count:
            return None
        key = hashlib.sha1(
            (row["instruction"] + "\n" + row["output"][:200]).encode()
        ).hexdigest()
        if key in seen:
            return None
        seen.add(key)
        produced += 1
        return row

    # Pass 1: architecture seeds (+ variants)
    for seed, variant in itertools.product(_seed_architectures(), _VARIANTS):
        out = architecture_answer(
            title=seed["title"],
            understanding=seed["understanding"] + f" {variant}",
            components=seed["components"],
            data_flow=seed["data_flow"],
            stack=seed["stack"],
            roadmap=seed["roadmap"],
            risks=seed["risks"],
            future=seed["future"],
            horizon_note=seed["horizon_note"],
        )
        row = make_sft_row(
            instruction=f"{seed['instruction']}. {variant}",
            output=out,
            domain=seed["domain"],
            horizon=seed["horizon"],
            tags=seed["tags"],
        )
        got = emit(row)
        if got:
            yield got
        if produced >= count:
            return

    # Pass 2: explanations (+ variants)
    for seed, variant in itertools.product(_topic_explains(), _VARIANTS):
        out = explain_answer(
            topic=seed["instruction"],
            body=seed["body"] + f"\n\nNote: {variant}",
            horizon=seed["horizon"],
        )
        row = make_sft_row(
            instruction=f"{seed['instruction']} ({variant})",
            output=out,
            domain=seed["domain"],
            horizon=seed["horizon"],
            tags=seed["tags"],
        )
        got = emit(row)
        if got:
            yield got
        if produced >= count:
            return

    # Pass 3: combinatorial domain topic prompts until count
    topics = [(d.id, d.horizon, t) for d in DOMAINS for t in d.topics]
    templates = [
        "Teach OM-1.0 about {topic} for Genesis-JARVIS",
        "As chief architect, outline how {topic} fits OM AI",
        "Create an implementation checklist for {topic} in OM-1.0",
        "Compare current vs research views of {topic}",
        "Design evaluation criteria for OM-1.0 on {topic}",
    ]
    for (domain, horizon, topic), tmpl, variant in itertools.product(
        topics, templates, _VARIANTS
    ):
        instr = tmpl.format(topic=topic) + f" — {variant}"
        out = explain_answer(
            topic=topic,
            body=(
                f"{topic} belongs in the OM Genesis knowledge map under domain `{domain}`. "
                f"Build software/agents first; connect hardware with gates; keep speculative "
                f"bio-digital ideas labeled as research. Variant focus: {variant}"
            ),
            horizon=horizon,
        )
        row = make_sft_row(
            instruction=instr,
            output=out,
            domain=domain,
            horizon=horizon,
            tags=[domain, "topic", topic.replace(" ", "-")[:32]],
        )
        got = emit(row)
        if got:
            yield got
        if produced >= count:
            return


def write_dataset(
    out_path: str | Path,
    *,
    count: int = 1000,
    also_chat_messages: bool = True,
) -> dict:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    domains: dict[str, int] = {}
    with out_path.open("w", encoding="utf-8") as f:
        for row in iter_examples(count=count):
            if also_chat_messages:
                # Dual format: keep instruction/output AND messages for SFT loader flexibility
                row = {
                    **row,
                    "messages": [
                        {"role": "system", "content": row["system"]},
                        {"role": "user", "content": row["instruction"]},
                        {"role": "assistant", "content": row["output"]},
                    ],
                    "prompt": row["instruction"],
                    "response": row["output"],
                }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            domains[row["domain"]] = domains.get(row["domain"], 0) + 1
            n += 1
    manifest = {
        "name": "omai-genesis-instruct-v1",
        "path": str(out_path),
        "count": n,
        "domains": domains,
        "system": GENESIS_SYSTEM,
        "note": (
            "Instruction dataset for OM-1.0 Genesis intelligence. "
            "Scale with higher --count; supplement with licensed textbooks/docs separately."
        ),
    }
    man_path = out_path.with_suffix(".manifest.json")
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Generate OM-1.0 Genesis SFT JSONL")
    p.add_argument(
        "--out",
        default="data/omai-genesis-v1/train/omai_genesis_instruct_v1.jsonl",
    )
    p.add_argument("--count", type=int, default=1000)
    args = p.parse_args(argv)
    man = write_dataset(args.out, count=max(1, args.count))
    print(json.dumps(man, indent=2))


if __name__ == "__main__":
    main()
