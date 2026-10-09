from om_ai.data_engine import (
    TextCleaner,
    Deduplicator,
    QualityScorer,
    KnowledgeClassifier,
)


text = """
Git is a distributed version control system
used by software developers.
"""


cleaner = TextCleaner()

clean = cleaner.clean(text)


print("CLEAN:")
print(clean)


quality = QualityScorer()

print(
    "QUALITY:",
    quality.score(clean)
)


classifier = KnowledgeClassifier()

print(
    "CLASS:",
    classifier.classify(clean)
)


dedupe = Deduplicator()

print(
    "FIRST:",
    dedupe.is_duplicate(clean)
)


print(
    "SECOND:",
    dedupe.is_duplicate(clean)
)