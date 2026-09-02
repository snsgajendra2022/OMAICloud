"""
OM-1.0 Knowledge Factory

Complete data generation pipeline.

Sources:

HuggingFace
Wikipedia
GitHub Code

Flow:

Source
 |
 ↓
Connector
 |
 ↓
Dataset Builder
 |
 ↓
OM Knowledge Dataset
"""

from __future__ import annotations


from typing import Iterator, Any


from om_ai.data_engine.pipeline import DatasetBuilder



class OMKnowledgeFactory:


    def __init__(
        self,
        output="data/om-knowledge-v1/train.jsonl"
    ):

        self.output = output

        self.builder = DatasetBuilder()



    def collect(
        self,
        connector
    ) -> Iterator[dict[str, Any]]:

        """
        Convert connector output
        into OM dataset format.
        """

        yield from connector.stream()



    def build(
        self,
        connector
    ) -> dict:


        records = self.collect(
            connector
        )


        result = self.builder.build_to_file(
            records,
            self.output
        )


        return result