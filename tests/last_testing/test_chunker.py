from om_ai.knowledge.processing.chunker import TextChunker


text = """
Git is a distributed version control system.
It helps developers manage source code history.
"""


chunker = TextChunker(
    chunk_size=10
)


chunks = chunker.split(
    text,
    "git"
)


for c in chunks:

    print(c.id)

    print(c.text)

    print("---")