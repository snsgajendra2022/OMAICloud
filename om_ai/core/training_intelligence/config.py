from __future__ import annotations

import os
from pathlib import Path


class TrainingIntelligenceConfig:
    """
    Dynamic OM training intelligence configuration.

    No fixed limits.
    Resources decide growth.
    """


    def __init__(self):

        self.enabled = self._bool(
            "OM_TRAINING_INTELLIGENCE_ENABLED",
            True
        )


        self.output_dir = Path(
            os.getenv(
                "OM_TRAINING_OUTPUT",
                "data/om-training"
            )
        )


        self.teacher_models = self._list(
            "OM_TEACHER_MODELS"
        )


        self.quality_threshold = float(
            os.getenv(
                "OM_TRAINING_MIN_QUALITY",
                "0.80"
            )
        )


        self.parallel_workers = int(
            os.getenv(
                "OM_TRAINING_PARALLELISM",
                "2"
            )
        )


        self.save_provenance = self._bool(
            "OM_TRAINING_PROVENANCE",
            True
        )


        self.deduplicate = self._bool(
            "OM_TRAINING_DEDUP",
            True
        )


    def _bool(
        self,
        key,
        default
    ):

        value = os.getenv(key)

        if value is None:
            return default

        return value.lower() in (
            "true",
            "1",
            "yes"
        )


    def _list(
        self,
        key
    ):

        value = os.getenv(
            key,
            ""
        )

        if not value:
            return []

        return [
            x.strip()
            for x in value.split(",")
            if x.strip()
        ]