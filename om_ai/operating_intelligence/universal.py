"""
Universal Intelligence Loop

User → Multimodal → Cognitive Understanding → Memory/Knowledge/Tools
→ Reasoning → Generation → Quality → Response → Self-improvement
"""
from __future__ import annotations

from typing import Any

from om_ai.core.intelligence import CognitiveIntelligence
from om_ai.multimodal.manager import MultimodalManager
from om_ai.generation import GenerationEngine
from om_ai.research.autonomous import AutonomousResearch


class UniversalIntelligence:
    def __init__(self) -> None:
        self.cognitive = CognitiveIntelligence()
        self.multimodal = MultimodalManager()
        self.generation = GenerationEngine()
        self.research = AutonomousResearch()

    def run(
        self,
        question: str = "",
        *,
        messages: list[dict] | None = None,
        path: str | None = None,
        mime: str | None = None,
        raw: bytes | None = None,
        memory_context: dict | list | None = None,
        user_profile: dict | None = None,
        project: dict | str | None = None,
    ) -> dict[str, Any]:
        q = (question or "").strip()
        stages = ["multimodal_understanding"]
        mm = None
        if path or raw:
            mm = self.multimodal.process(text=q, path=path, mime=mime, raw=raw, question=q)
            if mm.get("answer"):
                # Merge OCR text into question context for cognitive layer
                ocr_text = ""
                if mm.get("ocr") and mm["ocr"].get("text"):
                    ocr_text = str(mm["ocr"]["text"])[:2000]
                if ocr_text:
                    q = f"{q}\n\n[Image OCR]\n{ocr_text}".strip() if q else f"[Image OCR]\n{ocr_text}"

        stages.append("intelligence_manager")
        cognitive = self.cognitive.run(
            q or question,
            messages=messages,
            memory_context=memory_context,
            user_profile=user_profile,
            project=project,
        )

        stages.append("memory_knowledge_tools")
        research = self.research.maybe_research(
            q or question,
            understanding=cognitive.get("understanding"),
            knowledge_packets=(cognitive.get("context") or {}).get("memory_items"),
        )

        stages.append("reasoning_generation")
        answer = str(cognitive.get("answer") or "").strip()
        intent = str((cognitive.get("understanding") or {}).get("intent") or "")
        cap = str((cognitive.get("capability") or {}).get("id") or "")

        # Prefer multimodal vision answer when file was image and user asked about it
        if mm and mm.get("modality") == "image" and mm.get("answer"):
            if not q or any(
                x in (question or "").lower()
                for x in ("image", "screenshot", "diagram", "ocr", "extract", "what is in", "improve", "ui")
            ) or not answer:
                answer = mm["answer"].strip()

        if research.get("used") and research.get("summary"):
            answer = (answer + "\n\n**Research notes:**\n" + research["summary"]).strip()

        # Generation enrichment for diagram / code / docs intents
        gen_kind = None
        low_q = (question or "").lower()
        if any(x in low_q for x in ("diagram", "flowchart", "architecture diagram")):
            gen_kind = "diagram"
        elif intent in {"code_creation", "debugging"} and "prompt" not in intent:
            gen_kind = None  # cognitive coding path already handled
        elif "documentation" in low_q or "write docs" in low_q:
            gen_kind = "docs"
        elif "image prompt" in low_q or "generate image" in low_q:
            gen_kind = "image_prompt"

        generated = None
        if gen_kind:
            generated = self.generation.generate(
                kind=gen_kind,
                question=question,
                understanding=cognitive.get("understanding"),
            )
            answer = str(generated.get("content") or answer).strip()

        stages.append("quality_check")
        validation = cognitive.get("validation") or {}
        if float(validation.get("score") or 0) < 60 and mm and mm.get("answer"):
            answer = mm["answer"]

        stages.append("self_improvement")
        learning = self._learn(question, answer, cognitive, validation)

        return {
            "question": question,
            "answer": answer if answer.endswith("\n") else answer + "\n",
            "cognitive": cognitive,
            "multimodal": mm,
            "research": research,
            "generation": generated,
            "learning": learning,
            "stages": stages,
            "capability": cap,
            "intent": intent,
            "pipeline": [
                "multimodal",
                "understand",
                "memory_knowledge_tools",
                "reason",
                "generate",
                "verify",
                "learn",
            ],
        }

    def _learn(self, question: str, answer: str, cognitive: dict, validation: dict) -> dict[str, Any]:
        try:
            from om_ai.self_improvement.engine import SelfImprovementEngine

            eng = SelfImprovementEngine()
            # Soft record — engine APIs vary
            if hasattr(eng, "record"):
                eng.record(question, answer, validation)
            elif hasattr(eng, "memory") and hasattr(eng.memory, "store"):
                eng.memory.store(
                    {
                        "question": question,
                        "answer": answer[:1000],
                        "intent": (cognitive.get("understanding") or {}).get("intent"),
                        "score": validation.get("score"),
                    }
                )
            return {"stored": True}
        except Exception:
            # Always persist a lightweight experience file
            try:
                from pathlib import Path
                import json
                from datetime import datetime, timezone

                path = Path("data/om-memory/experience_log.json")
                path.parent.mkdir(parents=True, exist_ok=True)
                rows = json.loads(path.read_text()) if path.exists() else []
                if not isinstance(rows, list):
                    rows = []
                rows.append(
                    {
                        "question": question,
                        "intent": (cognitive.get("understanding") or {}).get("intent"),
                        "score": validation.get("score"),
                        "ok": validation.get("passed"),
                        "time": datetime.now(timezone.utc).isoformat(),
                    }
                )
                path.write_text(json.dumps(rows[-200:], indent=2))
                return {"stored": True, "path": str(path)}
            except Exception as exc:
                return {"stored": False, "error": str(exc)}
