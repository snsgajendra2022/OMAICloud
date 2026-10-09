from om_ai.data_engine.pipeline import (
    TextCleaner,
    Deduplicator,
    QualityScorer,
    KnowledgeClassifier
)


text = """
<h1>Git</h1>

Git is a distributed version control system.
"""


cleaner = TextCleaner()

clean = cleaner.clean(text)


print(clean)


quality = QualityScorer()

print(
    quality.score(clean)
)


classifier = KnowledgeClassifier()

print(
    classifier.classify(clean)
)


dup = Deduplicator()

print(
    dup.is_duplicate(clean)
)

print(
    dup.is_duplicate(clean)
)