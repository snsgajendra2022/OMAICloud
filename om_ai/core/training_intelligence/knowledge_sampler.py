from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from .models import TrainingQuestion



class KnowledgeSampler:
    """
    Dynamic knowledge discovery layer.

    Sources:

    - OM Knowledge Brain
    - Memory
    - Research
    - Existing datasets
    - Local documents

    No fixed topic list.
    """


    def __init__(
        self,
        knowledge_paths: list[str] | None = None,
    ):

        self.knowledge_paths = (
            knowledge_paths
            or [
                "data",
                "knowledge",
                "datasets",
            ]
        )



    def discover_sources(self):

        sources = []


        for location in self.knowledge_paths:

            path = Path(location)


            if not path.exists():

                continue



            for file in path.rglob("*"):

                if file.is_file():

                    sources.append(
                        file
                    )


        return sources



    def extract_text(
        self,
        file: Path
    ) -> str:


        try:

            if file.suffix.lower() in (
                ".txt",
                ".md",
                ".json",
                ".jsonl",
            ):

                return file.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )


        except Exception:

            pass


        return ""



    def detect_domain(
        self,
        text: str
    ) -> str:

        """
        Dynamic domain placeholder.

        Later connected with OM domain classifier.

        No keyword rules.
        """

        return "general"



    def create_question(
        self,
        content: str,
        source: str
    ) -> TrainingQuestion:


        question_id = hashlib.sha256(
            content.encode(
                "utf-8"
            )
        ).hexdigest()[:16]


        return TrainingQuestion(

            question=(
                "Create a deep explanation "
                "and practical understanding "
                f"from this knowledge:\n\n{content[:2000]}"
            ),

            domain=self.detect_domain(
                content
            ),

            metadata={

                "source":
                    str(source),

                "id":
                    question_id

            }

        )



    def sample(
        self,
        limit: int | None = None
    ):


        questions = []


        sources = (
            self.discover_sources()
        )


        for source in sources:


            text = self.extract_text(
                source
            )


            if not text.strip():

                continue



            questions.append(

                self.create_question(
                    text,
                    source
                )

            )


            if (
                limit
                and len(questions)
                >= limit
            ):

                break



        return questions