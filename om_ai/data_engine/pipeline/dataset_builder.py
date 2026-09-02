"""
OM-1.0 Data Engine
Dataset Builder

Production pipeline:

Connector
    |
    ↓
Cleaning
    |
    ↓
Deduplication
    |
    ↓
Quality Evaluation
    |
    ↓
Knowledge Classification
    |
    ↓
OM Dataset JSONL


Output format:

{
    "text": "...",
    "source": "...",
    "license": "...",
    "domain": "programming",
    "technology": "python",
    "quality_score": 0.92,
    "version": "om-knowledge-v1"
}
"""


from __future__ import annotations


from dataclasses import dataclass, asdict

from pathlib import Path

from typing import Iterator, Any

import json
import time


from .cleaner import TextCleaner
from .deduplicator import Deduplicator
from .quality import QualityScorer
from .classifier import KnowledgeClassifier



@dataclass(slots=True)
class DatasetRecord:

    text: str

    source: str = "unknown"

    license: str = "unknown"

    domain: str = "general"

    technology: str | None = None

    quality_score: float = 0.0

    version: str = "om-knowledge-v1"





class DatasetBuilder:


    def __init__(
        self,
        quality_threshold: float = 0.50,
        version: str = "om-knowledge-v1"
    ):

        self.cleaner = TextCleaner()

        self.deduplicator = Deduplicator()

        self.quality = QualityScorer()

        self.classifier = KnowledgeClassifier()

        self.quality_threshold = quality_threshold

        self.version = version



    def process_record(
        self,
        item: dict[str, Any]
    ) -> DatasetRecord | None:


        text = str(
            item.get("text", "")
        )


        if not text:

            return None



        # Cleaning

        text = self.cleaner.clean(
            text
        )


        if not self.cleaner.valid(
            text
        ):

            return None



        # Duplicate checking

        if self.deduplicator.is_duplicate(
            text
        ):

            return None



        # Quality scoring

        score = self.quality.score(
            text
        )


        if score < self.quality_threshold:

            return None



        # Classification

        classification = self.classifier.classify(
            text
        )



        return DatasetRecord(

            text=text,

            source=str(
                item.get(
                    "source",
                    "unknown"
                )
            ),

            license=str(
                item.get(
                    "license",
                    "unknown"
                )
            ),

            domain=classification.get(
                "domain",
                "general"
            ),

            technology=classification.get(
                "technology"
            ),

            quality_score=score,

            version=self.version

        )



    def build(
        self,
        records: Iterator[dict[str, Any]]
    ) -> Iterator[DatasetRecord]:


        for item in records:


            result = self.process_record(
                item
            )


            if result:

                yield result





    def save_jsonl(
        self,
        records: Iterator[DatasetRecord],
        output_path: str
    ) -> int:


        path = Path(
            output_path
        )


        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        count = 0



        with path.open(
            "w",
            encoding="utf-8"
        ) as file:


            for record in records:


                file.write(

                    json.dumps(
                        asdict(record),
                        ensure_ascii=False
                    )

                    +

                    "\n"

                )


                count += 1



        return count





    def build_to_file(
        self,
        records: Iterator[dict[str, Any]],
        output_path: str
    ) -> dict[str, Any]:


        start = time.time()


        processed = self.build(
            records
        )


        count = self.save_jsonl(
            processed,
            output_path
        )


        return {

            "status": "completed",

            "records": count,

            "output": output_path,

            "version": self.version,

            "time_seconds":
                round(
                    time.time() - start,
                    3
                )

        }