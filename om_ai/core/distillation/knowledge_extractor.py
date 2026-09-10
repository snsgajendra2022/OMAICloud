from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import hashlib


@dataclass
class KnowledgeItem:

    topic: str

    subtopic: str = ""

    concepts: list[str] = field(
        default_factory=list
    )

    facts: list[str] = field(
        default_factory=list
    )

    relationships: list[str] = field(
        default_factory=list
    )

    procedures: list[str] = field(
        default_factory=list
    )

    examples: list[str] = field(
        default_factory=list
    )

    code_patterns: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    source_teachers: list[str] = field(
        default_factory=list
    )

    confidence: float = 0.0

    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )

    knowledge_id: str = ""

    def __post_init__(self):

        if not self.knowledge_id:

            self.knowledge_id = hashlib.sha256(

                (
                    self.topic
                    +
                    self.subtopic
                )
                .encode()

            ).hexdigest()[:16]



class KnowledgeExtractor:
    """
    Converts approved responses into
    structured OM knowledge objects.

    This does not pretend to understand
    all knowledge using keyword rules.

    It creates a structured container.
    Semantic extraction can be enhanced
    using local teacher models.
    """


    def extract(
        self,
        topic: str,
        responses: list[dict],
    ) -> KnowledgeItem:


        item = KnowledgeItem(
            topic=topic
        )


        for response in responses:


            text = response.get(
                "response",
                ""
            )


            teacher = response.get(
                "teacher",
                "unknown"
            )


            if not text:
                continue


            item.source_teachers.append(
                teacher
            )


            item.concepts.extend(
                self._extract_concepts(
                    text
                )
            )


            item.facts.extend(
                self._extract_facts(
                    text
                )
            )


            item.examples.extend(
                self._extract_examples(
                    text
                )
            )


            if self._looks_like_code(
                text
            ):

                item.code_patterns.append(
                    text
                )


        item.source_teachers = list(
            set(
                item.source_teachers
            )
        )


        item.confidence = min(

            len(
                item.source_teachers
            )
            /
            3,

            1.0

        )


        return item



    def _extract_concepts(
        self,
        text: str
    ):


        lines = text.split(
            "."
        )


        return [

            line.strip()

            for line in lines

            if 3 < len(line.split()) < 15

        ][:10]



    def _extract_facts(
        self,
        text: str
    ):

        facts=[]


        for line in text.split(
            "\n"
        ):

            if any(
                word in line.lower()
                for word in [
                    "is",
                    "are",
                    "means",
                    "provides",
                    "used"
                ]
            ):

                facts.append(
                    line.strip()
                )


        return facts[:20]



    def _extract_examples(
        self,
        text: str
    ):

        return [

            line.strip()

            for line in text.split(
                "\n"
            )

            if "example" in line.lower()

        ]



    def _looks_like_code(
        self,
        text: str
    ):

        indicators=[

            "```",

            "def ",

            "class ",

            "function ",

            "import "

        ]


        return any(

            x in text

            for x in indicators

        )