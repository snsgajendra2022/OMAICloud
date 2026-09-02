"""
OM-1.0 Document Chunking Engine

Splits large documents into AI training/RAG friendly chunks.
"""


from __future__ import annotations

from dataclasses import dataclass



@dataclass(slots=True)
class Chunk:

    text: str

    chunk_id: int

    source: str = "unknown"



class DocumentChunker:


    def __init__(
        self,
        chunk_size: int = 800,
        overlap: int = 100
    ):

        self.chunk_size = chunk_size
        self.overlap = overlap



    def chunk(
        self,
        text: str,
        source: str = "unknown"
    ) -> list[Chunk]:

        words = text.split()

        chunks = []

        start = 0

        index = 0


        while start < len(words):

            end = start + self.chunk_size

            part = words[start:end]


            if not part:
                break


            chunks.append(
                Chunk(
                    text=" ".join(part),
                    chunk_id=index,
                    source=source
                )
            )


            index += 1


            start = end - self.overlap


        return chunks