from __future__ import annotations


from dataclasses import dataclass, field

from pathlib import Path

import os



@dataclass
class DistillationConfig:

    """
    Global configuration for OM Distillation Engine.

    No artificial dataset/model limits.
    Resource usage is controlled dynamically.
    """


    ollama_url: str = field(
        default_factory=lambda:
        os.getenv(
            "OM_OLLAMA_BASE_URL",
            "http://127.0.0.1:11434"
        )
    )


    teacher_models: list[str] = field(
        default_factory=lambda:

        [
            x.strip()

            for x in os.getenv(
                "OM_TEACHER_MODELS",
                ""
            )
            .split(",")

            if x.strip()

        ]
    )


    timeout: int = field(
        default_factory=lambda:

        int(
            os.getenv(
                "OM_TEACHER_TIMEOUT",
                "180"
            )
        )
    )


    output_path: Path = field(

        default_factory=lambda:

        Path(
            os.getenv(
                "OM_DISTILLATION_OUTPUT",
                "data/distillation"
            )
        )

    )


    store_raw: bool = field(

        default_factory=lambda:

        os.getenv(
            "OM_DISTILLATION_STORE_RAW",
            "true"
        ).lower()
        ==
        "true"

    )


    enable: bool = field(

        default_factory=lambda:

        os.getenv(
            "OM_DISTILLATION_ENABLED",
            "true"
        ).lower()
        ==
        "true"

    )


    def ensure_paths(self):

        self.output_path.mkdir(

            parents=True,

            exist_ok=True

        )