from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime


class ProgressTracker:
    """
    Tracks long running OM harvesting jobs.

    Supports:
    - resume
    - pause
    - statistics
    - incremental progress

    No maximum limits.
    """


    def __init__(
        self,
        path="data/distillation/progress.json"
    ):

        self.path = Path(path)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


    def load(self):

        if not self.path.exists():

            return {

                "completed": [],

                "failed": [],

                "pending": [],

                "statistics": {

                    "started": None,

                    "updated": None,

                    "processed": 0

                }

            }


        with open(
            self.path,
            encoding="utf-8"
        ) as f:

            return json.load(f)



    def save(
        self,
        state
    ):

        state["statistics"]["updated"] = (
            datetime.utcnow()
            .isoformat()
        )


        with open(
            self.path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                state,
                f,
                indent=2
            )



    def mark_completed(
        self,
        item_id
    ):

        state = self.load()


        if item_id not in state["completed"]:

            state["completed"].append(
                item_id
            )


        state["statistics"]["processed"] = (
            len(state["completed"])
        )


        self.save(state)



    def mark_failed(
        self,
        item_id,
        error
    ):

        state = self.load()


        state["failed"].append({

            "id": item_id,

            "error": str(error)

        })


        self.save(state)