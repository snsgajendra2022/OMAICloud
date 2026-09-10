"""Export distillation datasets to JSONL for OM SFT/DPO."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .distillation_state import DistillationState


class TrainingExporter:
    def __init__(self, state: DistillationState | None = None) -> None:
        self.state = state or DistillationState()

    def _append_jsonl(self, path: Path, row: dict[str, Any]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path

    def export(
        self,
        pack: dict[str, Any],
        *,
        output_dir: Path | str | None = None,
        also_training_buffer: bool = True,
    ) -> dict[str, Any]:
        out_root = Path(output_dir) if output_dir else self.state.root
        out_root.mkdir(parents=True, exist_ok=True)
        run_id = str(pack.get("run_id") or "run")
        slug = self.state.slug(str(pack.get("task") or run_id))
        written: dict[str, str] = {}
        exported = 0

        sft = pack.get("sft")
        if sft:
            task_path = out_root / f"{slug}_{run_id.split('_')[-1]}.jsonl"
            corpus = self.state.sft_dir / "distillation_sft.jsonl"
            self._append_jsonl(task_path, sft)
            self._append_jsonl(corpus, sft)
            written["sft_task"] = str(task_path)
            written["sft_corpus"] = str(corpus)
            exported += 1
            if also_training_buffer:
                buf = (
                    self.state.root.parent
                    / "om-memory"
                    / "advanced_learning"
                    / "training_buffer.jsonl"
                )
                self._append_jsonl(
                    buf,
                    {
                        "type": "sft",
                        "messages": sft.get("messages"),
                        "score": (sft.get("meta") or {}).get("score"),
                        "source": "step94_distillation",
                    },
                )
                written["training_buffer"] = str(buf)

        dpo = pack.get("dpo")
        if dpo:
            dpo_path = self.state.dpo_dir / "distillation_dpo.jsonl"
            self._append_jsonl(dpo_path, dpo)
            written["dpo_corpus"] = str(dpo_path)
            exported += 1

        ranked_path = self.state.ranked_dir / f"{run_id}.json"
        self.state.write_json(ranked_path, pack)
        written["ranked"] = str(ranked_path)
        meta = self.state.bump(run_id=run_id, exported=exported)
        return {"written": written, "exported": exported, "state": meta}
