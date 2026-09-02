from om_ai.data_engine.pipeline import DocumentChunker


text = """
Git is a distributed version control system.
It helps developers manage source code.
It supports branches, commits and collaboration.
"""


chunker = DocumentChunker(
    chunk_size=5,
    overlap=2
)


result = chunker.chunk(
    text,
    source="git"
)


for item in result:

    print(
        item.chunk_id,
        item.text
    )