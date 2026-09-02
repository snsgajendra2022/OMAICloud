"""
OM Knowledge Chunker

Splits large documents into searchable pieces.
"""


from dataclasses import dataclass



@dataclass
class DocumentChunk:

    id: str

    text: str

    source: str

    metadata: dict



class TextChunker:


    def __init__(
        self,
        chunk_size: int = 800,
        overlap: int = 100
    ):

        self.chunk_size = chunk_size
        self.overlap = overlap



    def split(
        self,
        text: str,
        source: str = "unknown"
    ):

        words = text.split()

        chunks = []

        start = 0

        index = 0


        while start < len(words):

            end = start + self.chunk_size


            content = " ".join(
                words[start:end]
            )


            chunks.append(

                DocumentChunk(

                    id=f"{source}_{index}",

                    text=content,

                    source=source,

                    metadata={

                        "size":
                        len(content)

                    }

                )

            )


            index += 1


            start = end - self.overlap


        return chunks