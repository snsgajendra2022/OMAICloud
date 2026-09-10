"""Build OM training records from ranked teacher knowledge."""
from __future__ import annotations

from typing import Any

from pathlib import Path
from datetime import datetime

import hashlib
import json


class DatasetBuilder:
    """Turn ranked distillation into SFT / DPO examples."""
    def __init__(
        self,
        output_path="data/training"
    ):

        self.output_path = Path(
            output_path
        )

        self.output_path.mkdir(
            parents=True,
            exist_ok=True
        )

    def build_om_answer(
        self,
        task: str,
        *,
        best: dict[str, Any] | None,
        comparison: dict[str, Any] | None = None,
    ) -> str:
        comparison = comparison or {}
        common = comparison.get("common_points") or []
        body = str((best or {}).get("text") or "").strip()
        if not body:
            return ""
        parts: list[str] = []
        if common:
            bullets = "\n".join(f"- {c}" for c in common[:10])
            parts.append(f"OM consensus themes:\n{bullets}")
        parts.append(body)
        parts.append(
            "\n(OM distilled answer — synthesized from ranked teacher outputs; "
            "verify against your environment before production use.)"
        )
        return "\n\n".join(p for p in parts if p).strip()

    def build_sft(
        self,
        task: str,
        *,
        best: dict[str, Any] | None,
        comparison: dict[str, Any] | None = None,
        run_id: str = "",
    ) -> dict[str, Any] | None:
        output = self.build_om_answer(task, best=best, comparison=comparison)
        if not output or not best:
            return None
        return {
            "instruction": task.strip(),
            "input": "",
            "output": output,
            "prompt": task.strip(),
            "response": output,
            "messages": [
                {"role": "user", "content": task.strip()},
                {"role": "assistant", "content": output},
            ],
            "meta": {
                "run_id": run_id,
                "teacher": best.get("provider"),
                "score": best.get("score"),
                "source": "step94_distillation",
            },
        }

    def build_dpo(
        self,
        task: str,
        *,
        best: dict[str, Any] | None,
        rejected: list[dict[str, Any]] | None = None,
        run_id: str = "",
    ) -> dict[str, Any] | None:
        if not best or not rejected:
            return None
        chosen = str(best.get("text") or "").strip()
        rej = next(
            (str(r.get("text") or "").strip() for r in rejected if str(r.get("text") or "").strip()),
            "",
        )
        if not chosen or not rej or rej == chosen:
            return None
        return {
            "prompt": task.strip(),
            "chosen": chosen,
            "rejected": rej,
            "meta": {
                "run_id": run_id,
                "chosen_teacher": best.get("provider"),
                "rejected_teacher": (rejected[0] or {}).get("provider") if rejected else None,
                "source": "step94_distillation",
            },
        }

    def build_pack(
        self,
        task: str,
        ranking: dict[str, Any],
        comparison: dict[str, Any],
        *,
        run_id: str,
    ) -> dict[str, Any]:
        best = ranking.get("best")
        sft = self.build_sft(task, best=best, comparison=comparison, run_id=run_id)
        dpo = self.build_dpo(
            task,
            best=best,
            rejected=ranking.get("rejected_candidates") or [],
            run_id=run_id,
        )
        return {
            "run_id": run_id,
            "task": task,
            "sft": sft,
            "dpo": dpo,
            "best_provider": (best or {}).get("provider"),
            "best_score": (best or {}).get("score"),
        }
    def create_id(
        self,
        data: dict
    ):

        raw = json.dumps(
            data,
            sort_keys=True
        )

        return hashlib.sha256(
            raw.encode()
        ).hexdigest()


    def append_jsonl(
        self,
        filename: str,
        data: dict
    ):

        file = (
            self.output_path
            /
            filename
        )


        data["created_at"] = (
            datetime.utcnow()
            .isoformat()
        )


        data["id"] = (
            self.create_id(data)
        )


        with open(
            file,
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                json.dumps(
                    data,
                    ensure_ascii=False
                )
                +
                "\n"
            )


        return str(file)



    def count_records(
        self,
        filename
    ):

        file = (
            self.output_path
            /
            filename
        )


        if not file.exists():

            return 0


        with open(
            file,
            encoding="utf-8"
        ) as f:

            return sum(
                1
                for _
                in f
            )